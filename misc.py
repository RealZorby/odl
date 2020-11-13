import importlib

def pPackage(args, compiler):
    if len(args) == 1:
        compiler.import_package(importlib.import_module(args[0]))
    elif len(args) == 2:
        compiler.import_from_package(importlib.import_module(args[1]))
    elif len(args) == 3:
        compiler.import_package(importlib.import_module(args[0]), args[2])
        

preprocessors = {"package": pPackage}