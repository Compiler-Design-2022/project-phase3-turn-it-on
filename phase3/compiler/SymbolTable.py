import random
import string

scope_counter = 0


class Class:
    def __init__(self, classname, superclass):
        self.name = classname
        self.superclass = superclass
        self.fields = []
        self.constructors = []
        self.methods = []

    def add_constructor(self, constructor):
        self.constructors.append(constructor)

    def add_method(self, method):
        self.methods.append(method)

    def add_method(self, field):
        self.fields.append(field)


def get_label():
    global scope_counter
    scope_counter += 1
    return "LABEL" + str(scope_counter)


class Method():
    def __int__(self, name, output_type, input_variables):
        self.name = name
        self.label = get_label() + "FUNC"
        self.output_type = output_type
        self.input_variables = input_variables

    def input_size(self):
        ans = 0
        # for input_type in inp


class Type():
    def __init__(self, name="int", array_length=0, inside_type=None):
        self.name = name
        self.length = None
        self.inside_type = None
        if name == "bool":
            self.size = 4
        elif name == "int":
            self.size = 4
        elif name == "ref":
            self.size = 4
            self.inside_type = inside_type
        elif name == "double":
            self.size = 8
        elif name == "string":
            self.size = 4  # its a pointer
            self.length = array_length
            self.inside_type = "char"
        elif name == "array":
            self.size = 4  # its a pointer
            self.length = array_length
            self.inside_type = inside_type
        else:
            raise ValueError  # type not found

    def __eq__(self, other):
        if self.inside_type is None:
            return self.name == other.name
        if self.length != other.length:
            return False
        return self.inside_type == other.inside_type

    def merge_type(self, other):
        return self  # TODO


class Variable():
    def __init__(self, name, type: Type):
        self.name = name
        self.type = type


class Scope():
    def __init__(self, for_scope=False, method_scope=False):
        self.variables = []
        scope_name = get_label()
        self.begin_label = scope_name + "_start"
        self.end_label = scope_name + "_end"
        self.for_scope = for_scope
        self.method_scope = method_scope

    def __str__(self):
        return self.begin_label + "(*)" + self.end_label

    def push_variable(self, variable: Variable):
        print("push variable : ", variable.name, variable.type.size)
        self.variables.append(variable)

    def last_variable(self):
        return self.variables[len(self.variables) - 1]

    def get_address_diff(self, name):
        offset = 0
        for i in range(len(self.variables) - 1, -1, -1):
            offset += self.variables[i].type.size
            if self.variables[i].name == name:
                return offset
        return None

    def pop_variable(self):
        variable = self.variables.pop()
        print("pop variable : ", variable.name, variable.type.size)

    def get_variable(self, name):
        for i in range(len(self.variables) - 1, -1, -1):
            if self.variables[i].name == name:
                return self.variables[i]
        return None

    def size(self):
        ans = 0
        for variable in self.variables:
            ans += variable.type.size
        return ans


class SymbolTable():
    def __init__(self):
        self.scope_stack: [Scope] = []
        self.vtable: [Method] = []

    def push_scope(self, scope: Scope):
        print("push scope ")
        self.scope_stack.append(scope)

    def get_method(self, name, input_types=None):
        pass

    def get_address_diff(self, name):
        offset = 0
        for i in range(len(self.scope_stack) - 1, -1, -1):
            if self.scope_stack[i].get_address_diff(name) is not None:
                print("LOL", name, offset + self.scope_stack[i].get_address_diff(name), offset)
                return offset + self.scope_stack[i].get_address_diff(name)
            offset += self.scope_stack[i].size()
        raise ValueError  # value doesn't declared

    def get_variable(self, name):
        for i in range(len(self.scope_stack) - 1, -1, -1):
            if self.scope_stack[i].get_variable(name) is not None:
                return self.scope_stack[i].get_variable(name)
        raise ValueError(name)  # value doesn't declared

    def last_scope(self) -> Scope:
        return self.scope_stack[len(self.scope_stack) - 1]

    def pop_scope(self):
        print("pop scope ")
        self.scope_stack.pop()

    def last_all_defined_scope(self) -> Scope:
        return self.all_defined_scope[len(self.all_defined_scope) - 1]
