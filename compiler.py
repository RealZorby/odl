import re, importlib

from . import builtin, misc

def shorten_indent(string, num=1):
    return str("".join(list(map(lambda x: x[num:]+"\n", string.split("\n")))))[:-1]

def translate_path(string):
    pieces = string.split(".")
    if len(pieces) > 1:
        return pieces[0] + "".join(list(map(lambda x: f".children['{x}']", pieces[1:])))

def decrement_path(path, mult=1):
    return "".join(list(map(lambda x: x+".", path.split(".")[:mult*-1])))[:-1]

def is_dunder(string):
    return string[0:2] == "__" and string[-2:len(string)] == "__"

class Compiler:

    def import_package(self, package, name=None):
        if not name: name = package.__name__
        setattr(self.modules, name, package)

    def import_from_package(self, package):
        for i in dir(package):
            if not is_dunder(i):
                setattr(self.modules, i, getattr(package, i))

    class Token:

        def __init__(self, path, cls_name, name, args, mentions):
            self.path = path
            self.cls_name = cls_name
            self.name = name
            self.args = args
            self.mentions = mentions
            self.sorted = False
        
        def __str__(self):
            return f"ODL Token {self.path}: <{self.cls_name} {self.name} {''.join(tuple(map(lambda x: str(x) + ' ', self.args)))[:-1]}>"
        
        def __getattr__(self, attr):
            return self.children[attr]

    def __init__(self):
        self.modules = builtin.void()
        self.root = builtin.void()
        self.tokens = []
        self.import_from_package(builtin)

    def split_body(self, string):
        lines = string.split("\n")
        out = []

        cur_obj = lines[0] + "\n"
        lines = lines[1:]
        for line in lines:
            if line[0] == " ":
                cur_obj += line + "\n"
            elif line[0:2] == "</":
                cur_obj += line + "\n"
                out.append(cur_obj[:-1])
                cur_obj = ""
            else:
                if cur_obj:
                    out.append(cur_obj[:-1])
                cur_obj = line + "\n"
        
        if cur_obj and cur_obj != "\n":
            out.append(cur_obj[:-1])
        return out

    def construct_body(self, parent, string, path):
        objs = self.split_body(string)

        for obj in objs:
            name, token = self.construct_object(obj, path)
            self.tokens.append(token)

    def split_args(self, string):
        args = []

        cur_arg = ""
        recrusion = 0
        for char in string:

            cur_arg += char
            if char == "<":
                recrusion += 1
            elif char == ">":
                recrusion -= 1
            elif char == " " and recrusion == 0:
                args.append(cur_arg[:-1])
                cur_arg = ""
            
        if cur_arg:
            args.append(cur_arg)
        
        return args

    def construct_args(self, args):
        mentions = []
        tokens = []

        for arg in args:
            if arg[0] == "@":
                mentions.append(builtin.mention(arg[1:]))
                tokens.append(builtin.mention(arg[1:]))
            elif re.match(r"[0-9\.]+", arg):
                tokens.append(builtin.int(arg))
            elif re.match(r"[\"'].*[\"']", arg):
                tokens.append(builtin.str(arg[1:-1]))
            elif arg[0] == "<":
                tokens.append(self.construct_object(arg, "")[1])
        
        return tokens, mentions

    def split_header(self, string):
        header = string[1:-1]
        pieces = header.split()
        cls_name, name = pieces[0:2]
        args_string = "".join(list(map(lambda x: x+" ", pieces[2:])))[:-1]

        try:
            args_func = eval(f"self.modules.{cls_name}.__odl_split_args__")
            args = args_func(args_string)
        except:
            args = self.split_args(args_string)
        
        return cls_name, name, args

    def construct_header(self, string):
        cls_name, name, args = self.split_header(string)

        try:
            args_func = eval(f"self.modules.{cls_name}.__odl_construct_args__")
            tokens, mentions = args_func(args)
        except:
            tokens, mentions = self.construct_args(args)
        
        return cls_name, name, tokens, mentions

    def split_object(self, string):
        header = ""
        body = ""

        recrusion = 0
        header_end = 0
        for x, char in enumerate(string):
            header += char
            
            if char == "<":
                recrusion += 1
            elif char == ">":
                recrusion -= 1
            
            if recrusion == 0:
                header_end = x
                break
                
        if len(string) > len(header):
            body = string[header_end+2:-4]

        return header, body

    def construct_object(self, string, path):
        header, body = self.split_object(string)
        cls_name, name, args, mentions = self.construct_header(header)
        if len(path): path += "." + name
        else: path += name
        token = self.Token(path, cls_name, name, args, mentions)
        body = shorten_indent(body)

        try:
            body_func = eval(f"self.modules.{cls_name}.__odl_construct_body__")
            body_func(token, body, path, self)
        except:
            self.construct_body(token, body, path)
        return name, token

    def sort_token(self, token, new):
        if not token.sorted:
            new.insert(0, token)
            token.sorted = True
            for mention in token.mentions:
                try:
                    eval(f"self.modules.{mention.path}")
                except AttributeError:
                    for t in self.tokens:
                        print(f"here <{t.path}> <{mention.path}>")
                        if t.path == mention.path:
                            print("yes")
                            self.sort_token(t, new)
                            break

    def sort_tokens(self):
        new = []

        for token in self.tokens:
            self.sort_token(token, new)
        
        print(*new)
        return new

    def bake_object(self, obj):
        clss = eval("self.modules." + obj.cls_name)

        objects = []
        for arg in obj.args:
            if isinstance(arg, builtin.mention):
                try:
                    objects.append(eval("self.modules." + arg.path))
                except AttributeError:
                    objects.append(eval("self.root." + arg.path))
            elif isinstance(arg, Compiler.Token):
                objects.append(self.bake_object(arg))
            else:
                objects.append(arg)
    
        try: init = clss.__odl_init_mode__
        except: init = 1

        if init: this = clss(*objects)
        else: this = clss.__odl_init__(obj, self)

        return this

    def bake(self):
        tokens = self.sort_tokens()

        for token in tokens:
            this = self.bake_object(token)
            path = eval("self.root" + decrement_path(token.path))
            setattr(path, token.name, this)

    def compile(self, string, globs={}):

        #process globals
        for glob in globs:
            setattr(self.root, glob, globs[glob])

        #prepare enviroment
        lines = string.split("\n")
        newstring = ""
        for line in lines:
            if line:
                if line[0] == "$":
                    args = line.split(" ")
                    cmd = args[0][1:]
                    if len(args) > 1: args = args[1:]
                    else: args = ()
                    misc.preprocessors[cmd](args, self)
                else: newstring += line + "\n"
        string = newstring[:-1]
        del newstring

        self.construct_body(self, string, "")
        self.bake()

        try:
            return self.root.main
        except AttributeError:
            raise EnvironmentError("ODL: missing main object.")