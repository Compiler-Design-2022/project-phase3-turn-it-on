import random
import string


class Type():
    def __init__(self, name, array_length=0, inside_type=None):
        self.name = name
        self.length = None
        self.inside_type = None
        if name == "int":
            self.size = 4
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


class Variable():
    def __init__(self, name, type: Type):
        self.name = name
        self.type = type


class Scope():
    def __init__(self):
        self.variables = []
        scope_name = "".join(
            [random.choice(string.ascii_lowercase + string.ascii_uppercase + string.ascii_letters) for i in range(3)])
        self.begin_lable = scope_name + "_start"
        self.end_labele = scope_name + "_end"

    def push_variable(self, variable: Variable):
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

    def size(self):
        ans = 0
        for variable in self.variables:
            ans += variable.size()
        return ans


class SymbolTable():
    def __init__(self):
        self.scope_stack: [Scope] = []
        self.vtable = None

    def push_scope(self, scope: Scope):
        self.scope_stack.append(scope)

    def get_address_diff(self, name):
        offset = 0
        for i in range(len(self.scope_stack) - 1, -1, -1):
            if self.scope_stack[i].get_address_diff(name) is not None:
                return offset + self.scope_stack[i].get_address_diff(name)
            offset += self.scope_stack[i].size()
        raise ValueError  # value doesn't declared

    def last_scope(self) -> Scope:
        return self.scope_stack[len(self.scope_stack) - 1]

    def pop_scope(self):
        self.scope_stack.pop()
