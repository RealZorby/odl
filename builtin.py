import importlib

class odl_:
    """the ODL compound"""

    def __init__(self, parent):
        self.parent = parent

    def appear(self):
        return self.parent
    
    def init(self, args):
        return self.parent(args)
    
    @staticmethod
    def construct_body(token, body, path, compiler):
        compiler.construct_body(token, body, path)



_int = int
_float = float
_str = str
_list = list
_tuple = tuple


class int(_int):
    """ODL 'int' class"""

    def __init__(self, num):
        _int.__init__(num)

class float(_float):
    """ODL 'float' class"""

    def __init__(self, num):
        _float.__init__(num)

class str(_str):
    """ODL 'str' class"""
    
    def __init__(self, string):
        _str.__init__(string)

class list(_list):
    """ODL 'list' class"""
    
    __odl_init_mode__ = 0

    def __odl_init__(token, compiler):
        return _list(token.args)

class tuple(_tuple):
    """ODL 'tuple' class"""

    __odl_init_mode__ = 0

    def __odl_init__(token, compiler):
        return _tuple(token.args)

class void:
    
    def __init__(self):
        pass

class func:

    class ODL(odl_):

        @staticmethod
        def construct_body(token, body, path, compiler):
            token.func = body
    
        def createFunction(sourceCode, args="", globs={}):
            s = "def __TheFunction__(%s):\n" % args
            s += "\t" + "\n\t".join(sourceCode.split('\n')) + "\n"
            # Byte-compilation (optional)
            byteCode = compile(s, "<string>", 'exec')  
            # Setup the local and global dictionaries of the execution
            # environment for __TheFunction__
            try:
                bis   = __builtins__.__dict__ # builtins
            except:
                bis = __builtins__
            locs  = {}
            # Setup a standard-compatible python environment
            bis["locals"]  = lambda: locs
            bis["globals"] = lambda: globs
            globs["__builtins__"] = bis
            globs["__name__"] = "SUBENV"
            globs["__doc__"] = sourceCode
            # Finally execute the def __TheFunction__ statement:
            eval(byteCode, globs, locs)
            # As a result, the function is defined as the item __TheFunction__
            # in the locals dictionary
            fct = locs["__TheFunction__"]
            # Attach the function to the globals so that it can be recursive
            del locs["__TheFunction__"]
            globs["__TheFunction__"] = fct
            # Attach the actual source code to the docstring
            fct.__doc__ = sourceCode
            return fct
    
    __odl_init_mode__ = 0

    def __odl_init__(token, compiler):
        return func.ODL.createFunction(token.func, ", ".join(token.args), {**compiler.root.__dict__, **compiler.modules.__dict__})



class mention:
    
    def __init__(self, path):
        self.path = path
