import inspect,logging,sys
from collections import OrderedDict
import traceback as tr
import ollama


logger = logging.getLogger(__name__)

class funcStruct:
    def __init__(self,func,name:str,doc:str,argDesc:OrderedDict,argType:OrderedDict,argDefi:OrderedDict):
        class argDef:
            def __init__(self,desc,cls,default):
                self.desc = desc
                self.type = cls
                self.default = default

        self.name = name
        self.doc = doc
        self.func = func
        self.args = OrderedDict()
        for k,desc in argDesc.items():
            self.args[k] = argDef(desc,argType[k],argDefi[k])

    def __str__(self):
        res = f"Name: {self.name}\nDescription: {self.doc}\n"
        for k,o in self.args.items():
            res = res+f"  {k} : {o.desc=} {o.type=} {o.default=}\n"
        return res


class AgentTool:
    def __init__(self,model:str):
        self.funcObj = {}
        self.model = model

    def evaluate(self,query):
        logger.info(f"[AgentTool.evaluate] {query=}")
        toolList = [
                {
                    'type':'function',
                    'function':{
                        'name':fname,
                        'description':fobj.doc,
                        'parameters':{
                            'type':'object',
                            'properties':{
                                argname:{
                                        'type':'string',
                                        'description':f"Desc: {argobj.desc}.\nData type: {argobj.type}\nDefault Value: {argobj.default}"
                                    } for argname,argobj in fobj.args.items()
                                }
                            },
                        'required':[]
                        }
                } for fname,fobj in self.funcObj.items()]
        ######################
        response = ollama.chat(model = self.model,
                            messages=query,
                            tools = toolList)
        resp = {}
        for obj in response.message:
            logger.info(f"[AgentTool.evaluate] {obj}")
            if obj[0]=='content' and len(obj[1])>0:
                resp['content'] = obj[1]
            elif obj[0]=='tool_calls' and obj[1] is not None:
                tmp = {}
                for i,tool in enumerate(obj[1]):
                    fobj = self.funcObj[tool.function.name]
                    args = tool.function.arguments
                    #sig = f"{tool.function.name}({','.join(list(args.values()))})"
                    a = {}
                    for k,v in args.items():
                        try:
                            a[k] = fobj.args[k].type(v)
                        except:
                            if v in tmp:
                                a[k] = tmp[v]
                            else:
                                pass
                    try:
                        r = fobj.func(**a)
                        tmp[f'evaluating'] = f"function name: {fobj.name}\nargs: {args}"
                        tmp[f'result'] = r
                    except:
                        tmp[f'evaluating'] = f"function name: {fobj.name}\nargs: {a}"
                        tmp[f'error'] = tr.format_exc()
                    break
                resp['tool'] = tmp
        return resp


    def funcDeclaration(self,**argDesc):
        assert all(isinstance(v,str) for k,v in argDesc.items()),"All arguments values should be string"
        def decorator(func):
            name = func.__name__
            doc = func.__doc__
            argtype = OrderedDict()
            argdef = OrderedDict()
            argdesc = OrderedDict()
            for k,v in inspect.signature(func).parameters.items():
                argdesc[k] = argDesc[k]
                argtype[k] = None if v.annotation is inspect._empty else v.annotation
                argdef[k] = None if v.default is inspect._empty else v.default
            self.funcObj[name] = funcStruct(func,name,doc,argdesc,argtype,argdef)
            logger.info(f"[AgentTool: {name}] {argtype=} {argdef=} {argdesc=}")
            def inner(*args,**kargs):
                logger.info(f"[AgentTool: Eval {name}] {args=} {kargs=}")
                return func(*args,**kargs)
            return inner
        return decorator


