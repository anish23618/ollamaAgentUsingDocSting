from agentClass import AgentTool
import json

# Demo example
test = AgentTool('hermes3:latest')
#######################################
#######################################
@test.funcDeclaration(x="first argument for addition, must be integer",
                        y="Second argument for addition, must be a number")
def add(x:int,y:int=0):
    """This function defines addition of two numbers. 
Given x and y add(x,y) returns x+y.
if y is not given it returns x.
"""
    return x+y

@test.funcDeclaration(x="first argument for multiplication, must be integer",
                        y="Second argument for multiplication, must be a number")
def mult(x:int,y:int=1):
    """This function defines multiplication of two numbers. 
Given x and y mult(x,y) returns x*y.
if y is not given it returns x.
"""
    return x*y
#######################################
#######################################
#######################################

query = "what is 1243432*343227+223555?"
message = [{'role':'user',
    'content':f'''Using the tools provided please answer the query:
{query}
'''}]
resp = test.evaluate(message)
print("response:", json.dumps(resp,indent=4))
txt = ""
for k,o in resp.items():
    if isinstance(o,str):
        txt = txt+f"{k} : {o}\n"
    elif isinstance(o,dict):
        txt = txt+f"{k} : {json.dumps(o,indent=4)}\n"

message.append({'role':'assistant','content':txt})
message.append({'role':'user',
    'content':f'''Does the previous step provides the answer for the query:
{query}
If not please provide the answer using the previous results and tools available.
'''
})

resp = test.evaluate(message)
print("response:", json.dumps(resp,indent=4))

