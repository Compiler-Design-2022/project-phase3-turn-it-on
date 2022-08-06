import copy
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
    return "LABL" + str(scope_counter)


def get_string_number():
    global string_number_counter
    string_number_counter += 1
    return "String" + str(string_number_counter)


def get_function_number():
    global function_number_counter
    function_number_counter += 1
    return str(function_number_counter)


class Method:
    def __init__(self, name, output_type, input_variables):
        self.name = name.replace("@", "")
        self.label = get_label() + "FUNC"
        self.output_type = output_type
        self.input_variables = copy.deepcopy(input_variables)

    def __str__(self):
        ans= f"name:{self.name}  label:{self.label} output_type:{self.output_type} input_types:"
        for var in self.input_variables:
            ans+=str(var)
        return ans

    def get_method_inputs_size(self):
        ans = 0
        for variable in self.input_variables:
            ans += variable.type.size
        return ans


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
        elif name == "void":
            self.size = 0
        else:
            # print(name)
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

    def __str__(self):
        return f" vn:{self.name} {self.type}"

class Scope():
    def __init__(self, for_scope=False, method_scope=False, method=None):
        self.variables = []
        scope_name = get_label()
        self.begin_label = scope_name + "_start"
        self.end_label = scope_name + "_end"
        if for_scope:
            self.continue_label = scope_name + "_continue"
        self.for_scope = for_scope
        self.method_scope = method_scope
        self.method = method
        if method_scope:
            self.push_variable(Variable("$RA", Type("int")))


    def push_variable(self, variable: Variable):
        # print("push variable : ", variable.name, variable.type.size)
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
        # print("pop variable : ", variable.name, variable.type.size)

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
        self.scope_function_declared: [Scope] = []

    def push_method(self, method: Method):
        # print("push method", method)
        self.vtable.append(method)

    def push_scope(self, scope: Scope):
        # print("push scope ")
        self.scope_stack.append(scope)
        if scope.method_scope:
            self.scope_function_declared.append(scope)

    def get_method(self, name, input_types=None):
        name = name.replace("@", "")
        # print(name, input_types)
        for method in self.vtable:
            # print(method)
            if method.name == name and len(input_types) == len(method.input_variables):
                good = True
                for var1, type2 in zip(method.input_variables, input_types):
                    if var1.type != type2:
                        good = False
                        break
                if good:
                    return method
        raise ValueError(f"couldn't find {name}")

    def get_address_diff(self, name):
        offset = 0
        for i in range(len(self.scope_stack) - 1, -1, -1):
            if self.scope_stack[i].get_address_diff(name) is not None:
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
        # print("pop scope ")
        self.scope_stack.pop()

