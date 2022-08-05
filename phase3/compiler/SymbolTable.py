import random
import string

scope_counter = 0
string_number_counter = 0
function_number_counter = 0


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


def get_string_number():
    global string_number_counter
    string_number_counter += 1
    return "String" + str(string_number_counter)


def get_function_number():
    global function_number_counter
    function_number_counter += 1
    return str(function_number_counter)


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
    def __init__(self, name="int", inside_type=None):
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
            self.inside_type = Type("char")
        elif name == "array":
            self.size = 4  # its a pointer
            self.inside_type = inside_type
        elif name == "char":
            self.size = 4
        else:
            raise ValueError  # type not found

    def __eq__(self, other):
        if other is None:
            return False
        if self.inside_type is None:
            return self.name == other.name
        return self.inside_type == other.inside_type

    def __str__(self):
        return "TYPE " + self.name + (str(self.inside_type) if self.inside_type is not None else " ")

    def merge_type(self, other, limit=None):
        if self.size != other.size:
            raise ValueError
        if self != other:
            raise ValueError

        if limit is not None and other.name not in limit:
            raise ValueError
        return self  # TODO


class Variable():
    def __init__(self, name, type: Type):
        self.name = name
        self.type = type


class Scope():
    def __init__(self, scope_name="", for_scope=False, method_scope=False, method_output_type=None):
        self.variables = []
        if scope_name == "":
            self.scope_name = get_label()
        else:
            self.scope_name = scope_name
        self.begin_label = self.scope_name + "_start"
        self.end_label = self.scope_name + "_end"
        self.for_scope = for_scope
        self.method_scope = method_scope
        self.method_input_types = []
        self.method_output_type = method_output_type
        self.continue_label = self.scope_name + "_continue"

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

    def get_method_inputs_size(self):
        ans = 0
        for type in self.method_input_types:
            ans += type.size
        return ans

    def add_method_input_type(self, type):
        self.method_input_types.append(type)


class SymbolTable():
    def __init__(self):
        self.scope_stack: [Scope] = []
        self.vtable: [Method] = []
        self.scope_function_declared: [Scope] = []

    def push_scope(self, scope: Scope):
        print("push scope ")
        self.scope_stack.append(scope)
        if scope.method_scope:
            self.scope_function_declared.append(scope)

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

    def last_function_scope(self) -> Scope:
        return self.scope_function_declared[len(self.scope_function_declared) - 1]

    def get_function_with_name_types(self, name, types):
        for scope in self.scope_function_declared:
            if scope.scope_name == name.replace("@", "") and scope.method_scope and types == scope.method_input_types:
                return scope.scope_name, scope
