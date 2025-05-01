from agentClass import AgentTool
import json,ollama,re
import traceback as tr

class modelChatTest(AgentTool):
    def __init__(self,model:str):
        super().__init__()
        self.model = model
    
    def _generate(self,querylist:list,argmap:dict = {}):
        toolList = self.genToolDetails()
        response = ollama.chat(model = self.model,
                               messages = querylist,
                               tools = toolList)
        result = {}
        i = 0
        for obj in response.message:
            print(">>",obj)
            if obj[0]=='content' and len(obj[1])>0:
                result[f'response_{i}'] = obj[1]
            elif obj[0]=='tool_calls' and obj[1] is not None:
                tmp = {}
                for j,tool in enumerate(obj[1]):
                    fname = tool.function.name
                    args = tool.function.arguments
                    result[f'response_{i}_{j}_executing'] = f"executing: {fname}({args})"
                    try:
                        r = self.evaluate(fname,args,argmap)
                        result[f'response_{i}_{j}_result'] = r
                    except:
                        err = tr.format_exc()
                        result[f'response_{i}_{j}_error'] = f"Error encountered while evaluating {fname}({args}). Error is:\n {err}"
            i += 1
        return result

    def _critic(self,query:str,history:list):
        prompt1 = """You are acting as a critic to determine if the answer to the query:

{query}

is obtained or not. If the answer is wrong or incomplete please respond with appropiately so that the worker can finish the work, and what extra needs to be done to get the answer.
If no further action needs to be taken please respond with "Done" only, without any further explaination.
""".replace('{query}',query)
        response = ollama.chat(model = self.model,messages = history+[{'role':'user','content':prompt1}])

        return [{'role':'critic','content':o[1]} for o in response.message if o[0]=='content']


    def query(self,query:str,history:list=[],argmap:dict = {}):
        prompt0 = """ You have multiple tools available to you. 
Use the tools to answer the query to best of your abilities. 
If the query cannot be answered in one step, please list down all the steps required for completing the task and perform the first step only.
You will have multiple oppurtunity to finish the task. The query is:
{query}
        """.replace("{query}",query)
        mapping = {k:v for k,v in argmap.items()}
        hist = history+[{'role':'user','content':prompt0}]
        while True:
            result = self._generate(hist,mapping)
            for k,v in result.items():
                if re.search(r"response\_\d+\_\d\_result",k) is not None:
                    mapping[k] = v
                hist.append({'role':'system','content':f"'{k}':'{v}'"})
            result = self._critic(query,hist)
            for o in result:
                print("[critic]",o)
            hist.extend(result)
            if any('Done' in o['content'] for o in result):
                break
        return hist



obj = modelChatTest('hermes3:latest') 
#obj = AgentTool()

@obj.funcDecorator(x="First number",y="Number to be added")
def add(x:int,y:int=0):
    '''Adds two integer x and y, and returns x+y.'''
    return x+y

@obj.funcDecorator(x="First number",y="Number to be subtracted")
def sub(x:int,y:int=0):
    '''subtracts y from x, and returns x-y.'''
    return x-y

@obj.funcDecorator(x="First number",y="Number to be multiplied")
def mult(x:int,y:int=1):
    '''Multiplies y to x, and returns x*y.'''
    return x*y

@obj.funcDecorator(x="First number",y="Number to be divided")
def div(x:int,y:int):
    '''Divide y from x, and returns x/y.'''
    return x/y

@obj.funcDecorator(x="First number",y="Number to moduloed")
def rem(x:int,y:int):
    '''Gives the reminder of x divided by y.'''
    return x%y



obj.setClass()

#################################
# direct calculation
# 34*3+56/7
argmap = {'x0':34,'x1':3,'x2':56,'x3':7}

r = obj.evaluate('mult',{'x':'x0','y':'x1'},argmap)
print(r)
argmap['r0'] = r

r = obj.evaluate('div',{'x':'x2','y':'x3'},argmap)
print(r)
argmap['r1'] = r

r = obj.evaluate('add',{'x':'r0','y':'r1'},argmap)
print(r)

###################################
#LLM query
argmap = {'x0':34,'x1':3,'x2':56,'x3':7}
query = "what is the result of 3423212*311245+1203436/6 ?"
resp = obj.query(query,[],argmap)
print("#"*20)
for o in resp:
    print(o)
