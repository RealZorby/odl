import os
from . import compiler

def compile(string, globs={}):
    compiler_obj = compiler.Compiler()
    return compiler_obj.compile(string, globs)

def load(path, globs={}):
    """Opens a specified (rel/abs) file and compiles its content."""

    try:
        file = open(path)
        content = file.read()
        file.close()
    except FileNotFoundError:
        try:
            file = open(os.getcwd() + "/" + path)
            content = file.read()
            file.close()
        except:
            raise FileNotFoundError("File '{}' was not found.".format(os.getcwd() + "/" + path))
    
    return compile(content, globs)