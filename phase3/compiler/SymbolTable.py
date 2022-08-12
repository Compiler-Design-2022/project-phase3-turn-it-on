import copy
import random
import string

scope_counter = 0
string_number_counter = 0
function_number_counter = 0


class Field:
    def __init__(self, access_mode, variable):
        self.access_mode = access_mode
        self.variable = variable


class ClassObj:
    all_classes = []

    def __init__(self, classname, interface=False):
        self.name = classname
        self.fields: [Field] = []
        self.init_code = ""
        self.par = None
        self.interface=interface
        self.methods: [Method] = []
        ClassObj.all_classes.append(self)

    def get_methods(self):
        methods = ClassObj.get_class_by_name(self.par).get_methods() if self.par is not None else []
        replace=[False] * len(methods)
        for f in self.methods:
            assign = False
            for i, met in enumerate(methods):
                if met.name.split(".")[1] == f.name.split(".")[1]:
                    methods[i] = f
                    replace[i]=True
                    assign = True
                    break
            if not assign:
                methods.append(f)
        if self.par is not None and ClassObj.get_class_by_name(self.par).interface:
            for i in range(len(replace)):
                assert replace[i]==True

        return methods

    def get_function_num(self):
        return len(self.get_methods())

    def get_function_id(self, name):
        methods = self.get_methods()
        for i, method in enumerate(methods):
            if method.name.split(".")[1] == name.split(".")[1]:
                return i
        raise ValueError(f"Couldn't find method {name} in {self.name} for function id")

    def add_method(self, method):
        self.methods.append(method)

    def get_fields_gen(self):
        if self.par is not None:
            for f in ClassObj.get_class_by_name(self.par).get_fields():
                yield f
        for field in self.fields:
            yield field

    def get_fields(self):
        ans = []
        for f in self.get_fields_gen():
            ans.append(f)
        return ans

    def is_child(self, class2):
        if class2.name == self.name:
            return True
        if self.par is None:
            return False
        return ClassObj.get_class_by_name(self.par).is_child(class2)

    def set_par(self, par):
        # print(f"SET PAR {self.name} to {par}")
        self.par = par

    def get_field_dist(self, field_name):
        size = 0
        offset = 0 if self.par is None else ClassObj.get_class_by_name(self.par).size()
        for field in self.fields:
            field: Field
            if field.variable.name == field_name:
                return size + offset
            size += field.variable.type.size
        if self.par is not None:
            return ClassObj.get_class_by_name(self.par).get_field_dist(field_name)
        raise ValueError

    def get_field_by_name(self, name):
        for field in reversed(self.fields):
            field: Field
            if field.variable.name == name:
                return field
        if self.par is not None:
            return ClassObj.get_class_by_name(self.par).get_field_by_name(name)
        raise ValueError(f"couldn't find field {name} in {self.name}")

    # in stack | self.1 self.2, ...., self.k, par.1, par.2, ..., par.k, par.par.1, par.par.2, ... , par.par.k
    def add_field(self, field):
        self.fields.append(field)

    def size(self):
        ans = 0
        for field in self.fields:
            ans += field.variable.type.size
        if self.par is not None:
            ans += ClassObj.get_class_by_name(self.par).size()
        return ans

    @staticmethod
    def get_class_by_name(name):
        for class_obj in ClassObj.all_classes:
            if class_obj.name == name:
                return class_obj
        raise ValueError(f"couldn't find class {name}, {len(name)}")


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
        ans = f"name:{self.name}  label:{self.label} output_type:{self.output_type} input_types:"
        for var in self.input_variables:
            ans += str(var)
        return ans

    def get_method_inputs_size(self):
        ans = 0
        for variable in self.input_variables:
            ans += variable.type.size
        return ans


class Type():
    def __init__(self, name="int", inside_type=None, class_name=None):
        self.name = name
        self.length = None
        self.inside_type = None
        self.class_name = None
        if name == "bool":
            self.size = 4
        elif name == "int":
            self.size = 4
        elif name == "ref":
            self.size = 4
            self.inside_type = inside_type
        elif name == "double":
            self.size = 4
        elif name == "string":
            self.size = 4  # its a pointer
            self.inside_type = Type("char")
        elif name == "array":
            self.size = 4  # its a pointer
            self.inside_type = inside_type
        elif name == "char":
            self.size = 4
        elif name == "class":
            self.size = 4
            self.class_name = class_name

        elif name == "void":
            self.size = 0
        else:
            # print(name)
            raise ValueError(f"couldn't find type{name}")  # type not found

    def __eq__(self, other):
        if other is None:
            return False
        if self.inside_type is None:
            if self.name == "class":
                if self.name == other.name:
                    class1 = ClassObj.get_class_by_name(self.class_name)
                    class2 = ClassObj.get_class_by_name(other.class_name)
                    return class2.is_child(class1)
                return False
            return self.name == other.name
        return self.inside_type == other.inside_type

    def __str__(self):
        return "TYPE " + self.name + " " + self.class_name if self.class_name is not None else "" + (
            str(self.inside_type) if self.inside_type is not None else " ")

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
        self.is_global = False

    def set_global(self):
        self.is_global = True

    def __str__(self):
        return f" vn:{self.name} {self.type}"


class Scope():
    def __init__(self, for_scope=False, method_scope=False, method=None, class_scope=False, class_obj=None):
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
            self.push_variable(Variable("$GSA", Type("int")))
        self.class_scope = class_scope
        self.class_obj = class_obj

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
        self.functions_list: [Method] = []
        self.class_list: [ClassObj] = []
        self.temp_class = None

    def get_last_class(self):
        for scope in reversed(self.scope_stack):
            scope: Scope
            if scope.class_scope:
                return scope.class_obj
        return None

    def push_class(self, class_obj: ClassObj):
        self.class_list.append(class_obj)

    def get_class(self, name):
        name = name.replace("@", "")
        for class_obj in self.class_list:
            if class_obj.name == name:
                return class_obj
        raise ValueError(f"don't have class {name}")

    def push_method(self, method: Method):
        # print("push method", method)
        self.functions_list.append(method)
        if method.name.find(".") != -1:
            ClassObj.get_class_by_name(method.name.split(".")[0]).add_method(method)

    def push_scope(self, scope: Scope):
        # print("push scope ")
        self.scope_stack.append(scope)

    def get_method(self, name, input_types=None):
        name = name.replace("@", "")
        if '.' in name:
            class_name = name.split('.')[0]
            method_name = name.split('.')[1]
            class_obj: ClassObj = ClassObj.get_class_by_name(class_name)
            try:
                id = class_obj.get_function_id(name)
                method = class_obj.get_methods()
                return method[id]
            except:
                raise ValueError(f"couldn't find {name} input-types:{' '.join(map(str, input_types))}")
        else:
            # print(name, input_types)
            for method in self.functions_list:
                # print(method)
                if method.name == name and len(input_types) == len(method.input_variables):
                    good = True
                    for var1, type2 in zip(method.input_variables, input_types):
                        if var1.type != type2:
                            good = False
                            break
                    if good:
                        return method
            raise ValueError(f"couldn't find {name} input-types:{' '.join(map(str, input_types))}")

    def get_method_tof(self, name):
        name = name.replace("@", "")
        class_name = name.split('.')[0]
        method_name = name.split('.')[1]
        class_obj: ClassObj = ClassObj.get_class_by_name(class_name)
        try:
            id = class_obj.get_function_id(name)
            method = class_obj.get_methods()
            return method[id]
        except:
            return None
        # raise ValueError(f"couldn't find {name} ")

    def get_address_diff(self, name):
        offset = 0
        for i in range(len(self.scope_stack) - 1, -1, -1):
            if self.scope_stack[i].get_address_diff(name) is not None:
                return offset + self.scope_stack[i].get_address_diff(name)
            offset += self.scope_stack[i].size()
        raise ValueError(f"couldn't find variable {name}")  # value doesn't declared

    def get_variable(self, name):
        for i in range(len(self.scope_stack) - 1, -1, -1):
            if self.scope_stack[i].get_variable(name) is not None:
                return self.scope_stack[i].get_variable(name)
        raise ValueError(name)  # value doesn't declared

    def get_variable_scope(self, name):
        for i in range(len(self.scope_stack) - 1, -1, -1):
            if self.scope_stack[i].get_variable(name) is not None:
                return self.scope_stack[i]
        raise ValueError(name)  # value doesn't declared

    def last_scope(self) -> Scope:
        return self.scope_stack[len(self.scope_stack) - 1]

    def pop_scope(self):
        # print("pop scope ")
        self.scope_stack.pop()
