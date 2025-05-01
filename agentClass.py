import inspect,logging,sys
import traceback as tr

logger = logging.getLogger(__name__)

class funcDef:
    def __init__(self,func,name:str,doc:str,argDesc:dict,argType:dict,argDefa:dict,cls = None):
        class argDef:
            def __init__(self,desc,dtype,default):
                self.desc = desc
                self.dtype = dtype
                self.default = default
        self.func = func
        self.name = name
        self.doc = doc
        self.cls = cls
        self.args = {k:argDef(desc,argType[k],argDefa[k]) for k,desc in argDesc.items()}

class AgentTool:
    def __init__(self):
        self.funcDef = {}

    def funcDecorator(self,**argDesc):
        assert all(isinstance(v,str) for k,v in argDesc.items()),"All arguments should be string only"
        def _funcDec(func):
            name = func.__name__
            doc = func.__doc__
            argType = {}
            argDefa = {}
            for k,v in inspect.signature(func).parameters.items():
                if k == 'self':
                    continue
                argType[k] = None if v.annotation is inspect._empty else v.annotation
                argDefa[k] = None if v.default is inspect._empty else v.default
            self.funcDef[name] = funcDef(func,name,doc,argDesc,argType,argDefa,None)
            logger.info(f"[AgentTool.funcDecorator] function name: {name}; doc-string: '''{doc}'''; argument list: {list(argType.keys())}")
            ###################
            def inner(*arg,**kargs):
                return func(*arg,**kargs)
            return inner
        return _funcDec
    
    def setClass(self):
        for fname,fobj in self.funcDef.items():
            func = fobj.func
            #print(fname,inspect.getmodule(func),func.__qualname__.rsplit(".",1))
            cls = getattr(inspect.getmodule(func),func.__qualname__.rsplit(".",1)[0])
            cls = cls if inspect.isclass(cls) else None
            fobj.cls = cls
            logger.info(f"[AgentTool.setClass] {fname} {cls}")
        return
    
    def genToolDetails(self):
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
                                        'description':f"Desc: {argobj.desc}.\nData type: {argobj.dtype}\nDefault Value: {argobj.default}"
                                    } for argname,argobj in fobj.args.items()
                                }
                            },
                        'required':[]
                        }
                } for fname,fobj in self.funcDef.items()]
        return toolList

    def evaluate(self,fname:str,kargs:dict,argmap:dict={}):
        if fname not in self.funcDef:
            raise ValueError("function name not found")
        fobj = self.funcDef[fname]
        # defining input of function
        fargs = {}
        for k,o in fobj.args.items():
            if k in kargs:
                w = kargs[k]
                fargs[k] = argmap[w] if w in argmap else (w if o.dtype is None else o.dtype(w))
            elif o.default is not None:
                fargs[k] = o.default
        r = None
        if fobj.cls is None:
            r = fobj.func(**fargs)
        else:
            if 'self' in kargs:
                w = kargs['self']
                w = argmap[w] if w in argmap else w
                if isinstance(kargs['self'],fobj.cls):
                    r = fobj.func(kargs['self'],**obj)
                else:
                    raise AssertionError(f"'self' does not maps to correct class for the function call {fobj.name}")
            else:
                flag = False
                for k,o in mapping.items():
                    if isinstance(o,fobj.cls):
                        r = fobj.func(o,**obj)
                        flag = True
                        break
                if not flag:
                    raise AssertionError(f"for the function call {fobj.name}, no appropiate instance of class {fobj.cls} found")
        return r
