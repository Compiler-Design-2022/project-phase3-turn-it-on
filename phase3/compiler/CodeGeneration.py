import random

from SymbolTable import SymbolTable, Scope, Variable, Type, get_label, get_string_number, get_function_number, Method, \
    ClassObj, Field
import lark
import copy

function_declaration_phase = True


class fake_parse_tree():
    def __init__(self, name):
        self.data = name
        self.children = []


def reset_function_declaration_phase():
    global function_declaration_phase
    function_declaration_phase = True


class Node_Return:
    def __init__(self, code=None, type=None, scope=None, text=None):
        self.code = code
        self.type = type
        self.scope = scope
        self.text = text


def cgen_token(token: lark.Token, symboltable: SymbolTable):
    type = Type()
    if token.value[0] == "\"":
        token.value = token.value.replace("@", "")
        type = Type("string")

        ans = ""
        token.value = token.value.replace("\\n", '\n')
        token.value = token.value.replace("\\t", '\t')
        for c in token.value:
            if c != '"':
                ans += c + "***"
            else:
                ans += '"'
        ans = ans.replace("\n", "\\n")
        ans = ans.replace("\t", "\\t")
        token.value = ans

    if token.value.startswith("mips"):
        token.value = token.value.lstrip("mips").replace("@", "")
        return Node_Return(code=token.value, type=None)

    return Node_Return(text=token.value, type=type)


def function_declaration(parse_tree, symbol_table: SymbolTable, height=0):
    if parse_tree.__class__ is lark.Token:
        return ""
    if parse_tree.data == "function_decl":
        symbol_table1 = SymbolTable()
        symbol_table1.push_scope(Scope())
        type_child = cgen(parse_tree.children[0], symbol_table1)
        symbol_table1 = SymbolTable()
        symbol_table1.push_scope(Scope())
        name_child = cgen(parse_tree.children[1], symbol_table1)
        symbol_table1 = SymbolTable()
        symbol_table1.push_scope(Scope())
        input_child = cgen(parse_tree.children[2], symbol_table1)
        function_name = name_child.text
        if symbol_table.temp_class is not None:
            input_child.type = [Variable("$THIS",
                                         Type("class", class_name=symbol_table.temp_class.name))] + input_child.type
            function_name = symbol_table.temp_class.name + "." + function_name

        method = Method(function_name, type_child.type, input_child.type)
        symbol_table.push_method(method)
        parse_tree.method = method
    if parse_tree.data == "variable" and height == 3:
        symbol_table1 = SymbolTable()
        symbol_table1.push_scope(Scope())
        symbol_table1.push_scope(Scope())
        variable_node = cgen(parse_tree, symbol_table1)
        var: Variable = symbol_table1.last_scope().last_variable()
        var.set_global()
        symbol_table.last_scope().push_variable(var)
        return variable_node.code

    if parse_tree.data == "field" and parse_tree.children[1].data == "variable_decl":
        assert symbol_table.temp_class is not None

        symbol_table1 = SymbolTable()
        symbol_table1.push_scope(Scope())
        symbol_table1.push_scope(Scope())
        access_mode = cgen(parse_tree.children[0], symbol_table1).text
        symbol_table1 = SymbolTable()
        symbol_table1.push_scope(Scope())
        symbol_table1.push_scope(Scope())
        variable_node = cgen(parse_tree, symbol_table1)
        var: Variable = symbol_table1.last_scope().last_variable()
        symbol_table.temp_class.add_field(Field(access_mode, var))
        symbol_table.temp_class.init_code += variable_node.code

    if parse_tree.data == "class_decl":
        symbol_table1 = SymbolTable()
        symbol_table1.push_scope(Scope())
        symbol_table1.push_scope(Scope())
        class_name = cgen(parse_tree.children[0], symbol_table1).text.replace("@", "")
        class_obj = ClassObj(class_name)
        if len(parse_tree.children) > 1 and parse_tree.children[1].data == "ident":
            class_par_name = cgen(parse_tree.children[1], symbol_table1).text.replace("@", "")
            class_obj.set_par(class_par_name)

        symbol_table.temp_class = class_obj
    code = ""
    for child in parse_tree.children:
        code += function_declaration(child, symbol_table, height + 1)
    if parse_tree.data == "program":
        parse_tree.code = code
        global function_declaration_phase
        function_declaration_phase = False
    if parse_tree.data == "class_decl":
        symbol_table.push_class(symbol_table.temp_class)
        parse_tree.class_obj = symbol_table.temp_class
        symbol_table.temp_class = None
    return code


def cgen(parse_tree, symbol_table: SymbolTable):
    if parse_tree.__class__ is lark.Token:
        return cgen_token(parse_tree, symbol_table)

    # print("^" * 60, parse_tree.data, parse_tree._meta)
    before_enter(parse_tree, symbol_table)
    children_return = []
    for child in parse_tree.children:
        child_return = cgen(child, symbol_table)
        children_return.append(child_return)

    scope = symbol_table.last_scope()
    # print(len(symbol_table.scope_stack))
    gen: Node_Return = after_enter(parse_tree, symbol_table, children_return)
    gen.scope = scope
    return gen


def before_enter(parse_tree, symbol_table):
    if parse_tree.data == "stmt" or parse_tree.data == "stmtblock":
        new_scope = Scope()
        symbol_table.push_scope(new_scope)
    elif parse_tree.data == "whilestmt":
        new_scope = Scope(for_scope=True)
        symbol_table.push_scope(new_scope)
    elif parse_tree.data == "forstmt":
        new_scope = Scope(for_scope=True)
        symbol_table.push_scope(new_scope)
    elif parse_tree.data == "function_decl":
        symbol_table.push_scope(Scope(method_scope=True, method=parse_tree.method))
        if '.' in parse_tree.method.name:  # class function
            symbol_table.last_scope().push_variable(Variable("$THIS",
                                                             Type("class",
                                                                  class_name=symbol_table.get_last_class().name)))
    elif parse_tree.data == "normal_function_call" or parse_tree.data == "class_function_call":
        symbol_table.last_scope().push_variable(Variable("__IGNORE_RA", Type("int")))
        symbol_table.last_scope().push_variable(Variable("__IGNORE_GSA", Type("int")))
        if parse_tree.data == "normal_function_call" and symbol_table.get_last_class() is not None:
            # self function call
            class_function_name = symbol_table.get_last_class().name + "." + parse_tree.children[0].children[0].value
            if symbol_table.get_method_tof(class_function_name) is not None:
                parse_tree.data = "class_function_call"
                parse_tree.children = [fake_parse_tree("this_expr")] + parse_tree.children
                # print("CHANGE CODE!", parse_tree.data, len(parse_tree.children))



    elif parse_tree.data == "class_decl":
        symbol_table.push_scope(Scope(class_scope=True, class_obj=parse_tree.class_obj))
        for f in parse_tree.class_obj.get_fields():
            # print(f"PUSH VARIABLE {v}")
            if f.access_mode == "private":
                f.variable = Variable("IT IS PROTECTED", f.variable.type)
            symbol_table.last_scope().push_variable(f.variable)


def after_enter(parse_tree, symbol_table, children):
    """ variable: type ident """
    if parse_tree.data == "type":
        if children[0].text == None:
            return Node_Return(type=Type("array", inside_type=children[0].type))
        if len(children[0].text) > 0 and children[0].text[0] == "@":
            return Node_Return(type=Type("class", class_name=children[0].text[1:]))

        return Node_Return(code="", type=Type(children[0].text))
    elif parse_tree.data == "ident":
        return Node_Return(code="", type=None, text=children[0].text)
    elif parse_tree.data == "null":
        return Node_Return(code="", type=None, text="")
    elif parse_tree.data == "len_expr":
        inside_code = children[0].code
        symbol_table.last_scope().pop_variable()
        symbol_table.last_scope().push_variable(Variable("__IGNORE_len_expr", Type("int")))
        code = f'''{inside_code}
                    \t lw $t1, {children[0].type.size}($sp)
                    \t addi $sp, $sp, {children[0].type.size}
                    \t lw $t1, 0($t1)
                    \t sw $t1, 0($sp)
                    \t addi $sp, $sp, -4
                '''
        return Node_Return(code=code, type=Type("int"))

    # constant_token: INT | STRING | base16 | "null"
    elif parse_tree.data == "constant_token":
        code = ""
        if children[0].type.name == "string":
            string_name = f"{symbol_table.last_scope().begin_label}_{get_string_number()}"
            code += f'''
                        .data
                        \t {string_name}: .word {(len(children[0].text) - 2) // 4}
                        \t IGNORE__{get_label()}: .asciiz  {children[0].text}
                        .text
                        \t la $t0, {string_name}
                        \t sw $t0, 0($sp)
                        \t addi $sp, $sp, -4
                    '''
            symbol_table.last_scope().push_variable(Variable("__IGNORE_string_constant_token", children[0].type))
        return Node_Return(code=code, type=children[0].type, text=children[0].text)

    # boolconstant_true: "true"
    elif parse_tree.data == "boolconstant_true":
        return Node_Return(code="", type=Type("bool"), text=1)

    # boolconstant_false: "false"
    elif parse_tree.data == "boolconstant_false":
        return Node_Return(code="", type=Type("bool"), text=0)


    # variable: type ident
    elif parse_tree.data == "variable":
        if len(symbol_table.scope_stack) > 1 or function_declaration_phase:
            variable = Variable(children[1].text, children[0].type)
            # print(symbol_table.get_last_class() is None or function_declaration_phase)
            if not symbol_table.last_scope().class_scope or function_declaration_phase:
                symbol_table.last_scope().push_variable(variable)

            if children[0].type.name == "double":
                double_name = "__IGNORE" + get_label()
                code = f''' 
                            .data
                            {double_name}: .float 0.0
                            .text
                            \t la $t0, {double_name}
                            \t lw $t1, 0($t0)
                            \t sw $t1, 0($sp)
                            \t addi $sp, $sp, -4
                        '''
            else:
                code = f'''
                            sub $t1, $t1, $t1
                            sw $t1, 0($sp)
                            addi $sp, $sp, -{variable.type.size}
                        '''
            return Node_Return(code=code, type=children[0].type, text=children[1].text)
        else:
            return Node_Return(code="", type=children[0].type, text=children[1].text)

    # lvalue: ident |  class_val | array_val
    if parse_tree.data == "lvalue":  # DOTO array, class
        if parse_tree.children[0].data != "ident":
            return children[0]
        diff = symbol_table.get_address_diff(children[0].text)
        var: Variable = symbol_table.get_variable(children[0].text)
        if not var.is_global:
            if symbol_table.get_variable_scope(children[0].text).class_scope:
                diff = None
                diff_to_this = symbol_table.get_address_diff("$THIS")
                diff_from_this = symbol_table.get_variable_scope(children[0].text).get_address_diff(
                    children[0].text) - var.type.size
                # print(f"READ {diff_from_this} to get {var.name}")
                code = f'''
                                        #load THIS address
                                        \t addi $t0, $sp, {diff_to_this}
                                        #load THIS
                                        \t lw $t0, 0($t0)
                                        \t lw $t0, 0($t0)
                                        #load var address
                                        \t addi $t0, $t0, {diff_from_this}
                                        \t sw $t0, 0($sp)
                                        \t addi $sp, $sp, -4
                                    '''
                symbol_table.last_scope().push_variable(Variable("__IGNORE_class_lvalue", var.type))
                return Node_Return(code=code, type=Type("ref", inside_type=var.type))
            else:
                code = f'''
                            \t addi $t0, $sp, {diff}
                            \t sw $t0, 0($sp)
                            \t addi $sp, $sp, -4
                        '''
                symbol_table.last_scope().push_variable(Variable("__IGNORE_lvalue", var.type))
                return Node_Return(code=code, type=Type("ref", inside_type=var.type))
        else:
            diff_to_gsa = symbol_table.get_address_diff("$GSA")
            diff_from_gsa = symbol_table.scope_stack[0].get_address_diff(children[0].text)
            # print(f" for global {children[0].text} get {diff_from_gsa}")
            code = f'''
                        #load GSA address
                        \t addi $t0, $sp, {diff_to_gsa}
                        #load GSA
                        \t lw $t0, 0($t0)
                        #load var address
                        \t addi $t0, $t0, {diff_from_gsa}
                        \t sw $t0, 0($sp)
                        \t addi $sp, $sp, -4
                    '''
            symbol_table.last_scope().push_variable(Variable("__IGNORE_global_lvalue", var.type))
            return Node_Return(code=code, type=Type("ref", inside_type=var.type))

    # new_array_expr: "NewArray" "(" expr "," type ")"
    elif parse_tree.data == "new_array_expr":  # TODO differrent type different code
        expr_code = children[0].code

        code = f'''#new_array_expr cal size
        {expr_code}
            #new_arra expr cal size END
            #new array expr get memory
                    \t lw $t0, {children[0].type.size}($sp)
                    \t move $t8, $t0
                    \t sub $t1, $t1, $t1 
                    \t addi $t1, $t1, {children[1].type.size}
                    \t mul $t0, $t0, $t1
                    \t addi $t0, $t0, {Type("int").size}
                    \t move $t4, $t0
                    \t move $a0, $t0
                    \t li $v0, 9 
                    \t syscall
                    \t move $t6, $v0
                    \t lw $t0, {children[0].type.size}($sp)
                    \t sw $t0 ,0($v0)
                    \t sw $v0, {children[0].type.size}($sp)
            #new array expr get memory END
                '''

        assert children[0].type == Type("int")
        return Node_Return(code=code, type=Type("array", inside_type=children[1].type))

    elif parse_tree.data == "new_expr":
        class_name = children[0].text
        class_obj = symbol_table.get_class(class_name)
        symbol_table.last_scope().push_variable(
            Variable("__IGNORE_CLASS_ADDRESS", Type("class", class_name=class_obj.name)))
        # print(f"GET {class_obj.size()}byte for {class_name}")
        code = f'''#new_expr class {class_name}
            #new class expr get memory
                    \t li $t0, {class_obj.size()}
                    \t move $a0, $t0
                    \t li $v0, 9 
                    \t syscall
                    \t sw $v0, 0($sp)
                    \t addi $sp, $sp, -4
                    
                    \t li $t0, {len(class_obj.methods)*4}
                    \t move $a0, $t0
                    \t li $v0, 9 
                    \t syscall
                    \t sw $v0, 0($sp)
                    \t addi $sp, $sp, -4
                    
                    \t li $t0, {8}
                    \t move $a0, $t0
                    \t li $v0, 9 
                    \t syscall
                    \t sw $v0, 0($sp)
                    \t addi $sp, $sp, -4
                    
                    
                    \t lw $t0, 12($sp)
                    \t lw $t1, 8($sp)
                    \t lw $t2, 4($sp)
                    \t addi $sp, $sp, 12
                    
                    \t sw $t0, 0($t2)
                    \t sw $t1, 4($t2)
                    
                    \t sw $t2, 0($sp)
                    \t addi $sp, $sp, -4
                    
            #new class expr get memory END
                '''
        return Node_Return(code=code, type=Type("class", class_name=class_obj.name))


    # array_val: expr "[" expr "]"
    elif parse_tree.data == "array_val":
        array_expr_code = children[0].code
        index_expr_code = children[1].code
        symbol_table.last_scope().pop_variable()
        symbol_table.last_scope().pop_variable()
        symbol_table.last_scope().push_variable(
            Variable("__IGNORE_array_val", Type("ref", inside_type=children[0].type.inside_type)))
        code = f'''#array val load array
                    {array_expr_code} 
                    #array val load array END
                    #array val index load 
                    {index_expr_code}
                    #array val index load END
                    #array val start
                    \t lw $t0, {children[1].type.size}($sp)
                    \t lw $t1, {children[1].type.size + children[0].type.size}($sp)
                    \t li $t2, {children[0].type.size} # it is 4 
                    \t mul $t0, $t0, $t2
                    \t add $t0, $t0, $t1
                    \t addi $sp, $sp, {children[1].type.size + children[0].type.size}
                    \t addi $t0, $t0, {Type("int").size}
                    \t sw $t0, 0($sp)
                    \t addi $sp, $sp, -4
                    #array val end
                '''
        assert children[1].type == Type("int")
        return Node_Return(code=code, type=Type("ref", inside_type=children[0].type.inside_type))

    elif parse_tree.data == "this_expr":
        diff_to_this = symbol_table.get_address_diff("$THIS")
        symbol_table.last_scope().push_variable(
            Variable("__IGNORE_THIS_VALUE", Type("class", class_name=symbol_table.get_last_class().name)))
        code = f'''
                                #load THIS address
                                \t addi $t0, $sp, {diff_to_this}
                                #load THIS
                                \t lw $t0, 0($t0)
                                \t sw $t0, 0($sp)
                                \t addi $sp, $sp, -4
                                '''
        return Node_Return(code=code, type=Type("class", class_name=symbol_table.get_last_class().name))


    elif parse_tree.data == "class_val":
        class_ref_builder = children[0].code
        field_name = children[1].text
        class_obj: ClassObj = symbol_table.get_class(children[0].type.class_name)
        field = class_obj.get_field_by_name(field_name)
        symbol_table.last_scope().pop_variable()
        symbol_table.last_scope().push_variable(
            Variable("__IGNORE_class_val", Type("ref", inside_type=field.variable.type)))
        # print(f"GET {class_obj.get_field_dist(field_name)} for {field_name} in class {class_obj.name}")
        code = f'''#class val load class 
                    {class_ref_builder} 
                    #class val load class END
                    #class val start
                    \t lw $t0, {children[0].type.size}($sp)
                    \t lw $t0, 0($t0)
                    \t addi $sp, $sp, 4
                    \t addi $t0, $t0, {class_obj.get_field_dist(field_name)}
                    \t sw $t0, 0($sp)
                    \t addi $sp, $sp, -4
                    #class val end
                '''
        return Node_Return(code=code, type=Type("ref", inside_type=field.variable.type))

    # assignment_expr_empty: lvalue "=" expr
    elif parse_tree.data == "assignment_expr_empty":
        variable_code = children[0].code
        expr_code = children[1].code
        symbol_table.last_scope().pop_variable()
        symbol_table.last_scope().pop_variable()
        symbol_table.last_scope().push_variable(Variable("__IGNORE_assignment_expr_empty", children[1].type))
        try:
            assert children[0].type.inside_type == children[1].type
        except:
            print(children[0].type.inside_type)
            print(children[1].type)
            raise ValueError
        code = f'''{variable_code} {expr_code}
                    \t lw $t0, {children[1].type.size}($sp)
                    \t lw $t1, {children[1].type.size + children[0].type.size}($sp)
                    \t sw $t0, 0($t1)
                    \t addi $sp, $sp, {children[1].type.size + children[0].type.size}
                    \t sw $t0, 0($sp)
                    \t addi $sp, $sp, -4
                '''
        return Node_Return(code=code, type=children[1].type, text="assignment")

    # assignment_expr_with_plus: lvalue "+=" expr
    elif parse_tree.data == "assignment_expr_with_plus":
        variable_code = children[0].code
        expr_code = children[1].code
        symbol_table.last_scope().pop_variable()
        symbol_table.last_scope().pop_variable()
        symbol_table.last_scope().push_variable(Variable("__IGNORE_assignment_expr_with_plus", children[1].type))
        assert children[0].type.inside_type == children[1].type
        if children[1].type.name == "double" or (
                children[1].type.name == "ref" and children[1].type.inside_type == "double"):
            code = f'''{variable_code} {expr_code}
                        \t lw $t0, {children[1].type.size}($sp)
                        \t lw $t1, {children[1].type.size + children[0].type.size}($sp) 
                        \t mtc1 $t0, $f0
                        \t lw $t2, 0($t1)
                        \t mtc1 $t2, $f2
                        \t add.s $f0, $f2, $f0
                        \t mfc1 $t0, $f0
                        \t sw $t0, 0($t1)
                        \t addi $sp, $sp, {children[1].type.size + children[0].type.size}
                        \t sw $t0, 0($sp)
                        \t addi $sp, $sp, -4
                    '''
            return Node_Return(code=code, type=Type("double"), text="assignment")
        else:
            code = f'''{variable_code} {expr_code}
                        \t lw $t0, {children[1].type.size}($sp)
                        \t lw $t1, {children[1].type.size + children[0].type.size}($sp)
                        \t lw $t2, 0($t1)
                        \t add $t0, $t0, $t2
                        \t sw $t0, 0($t1)
                        \t addi $sp, $sp, {children[1].type.size + children[0].type.size}
                        \t sw $t0, 0($sp)
                        \t addi $sp, $sp, -4
                    '''
            return Node_Return(code=code, type=children[1].type, text="assignment")

    # assignment_expr_with_min: lvalue "-=" expr
    elif parse_tree.data == "assignment_expr_with_min":
        variable_code = children[0].code
        expr_code = children[1].code
        symbol_table.last_scope().pop_variable()
        symbol_table.last_scope().pop_variable()
        symbol_table.last_scope().push_variable(Variable("__IGNORE_assignment_expr_with_min", children[1].type))
        assert children[0].type.inside_type == children[1].type
        if children[1].type.name == "double" or (
                children[1].type.name == "ref" and children[1].type.inside_type == "double"):
            code = f'''{variable_code} {expr_code}
                        \t lw $t0, {children[1].type.size}($sp)
                        \t lw $t1, {children[1].type.size + children[0].type.size}($sp) 
                        \t mtc1 $t0, $f0
                        \t lw $t2, 0($t1)
                        \t mtc1 $t2, $f2
                        \t sub.s $f0, $f2, $f0
                        \t mfc1 $t0, $f0
                        \t sw $t0, 0($t1)
                        \t addi $sp, $sp, {children[1].type.size + children[0].type.size}
                        \t sw $t0, 0($sp)
                        \t addi $sp, $sp, -4
                    '''
            return Node_Return(code=code, type=Type("double"), text="assignment")
        else:
            code = f'''{variable_code} {expr_code}
                        \t lw $t0, {children[1].type.size}($sp)
                        \t lw $t1, {children[1].type.size + children[0].type.size}($sp)
                        \t lw $t2, 0($t1)
                        \t sub $t0, $t2, $t0
                        \t sw $t0, 0($t1)
                        \t addi $sp, $sp, {children[1].type.size + children[0].type.size}
                        \t sw $t0, 0($sp)
                        \t addi $sp, $sp, -4
                    '''
            return Node_Return(code=code, type=children[1].type, text="assignment")

    # assignment_expr_with_mul: lvalue "*=" expr
    elif parse_tree.data == "assignment_expr_with_mul":
        variable_code = children[0].code
        expr_code = children[1].code
        symbol_table.last_scope().pop_variable()
        symbol_table.last_scope().pop_variable()
        symbol_table.last_scope().push_variable(Variable("__IGNORE_assignment_expr_with_mul", children[1].type))
        assert children[0].type.inside_type == children[1].type
        if children[1].type.name == "double" or (
                children[1].type.name == "ref" and children[1].type.inside_type == "double"):
            code = f'''{variable_code} {expr_code}
                        \t lw $t0, {children[1].type.size}($sp)
                        \t lw $t1, {children[1].type.size + children[0].type.size}($sp) 
                        \t mtc1 $t0, $f0
                        \t lw $t2, 0($t1)
                        \t mtc1 $t2, $f2
                        \t mul.s $f0, $f2, $f0
                        \t mfc1 $t0, $f0
                        \t sw $t0, 0($t1)
                        \t addi $sp, $sp, {children[1].type.size + children[0].type.size}
                        \t sw $t0, 0($sp)
                        \t addi $sp, $sp, -4
                    '''
            return Node_Return(code=code, type=Type("double"), text="assignment")
        else:
            code = f'''{variable_code} {expr_code}
                        \t lw $t0, {children[1].type.size}($sp)
                        \t lw $t1, {children[1].type.size + children[0].type.size}($sp)
                        \t lw $t2, 0($t1)
                        \t mul $t0, $t2, $t0
                        \t sw $t0, 0($t1)
                        \t addi $sp, $sp, {children[1].type.size + children[0].type.size}
                        \t sw $t0, 0($sp)
                        \t addi $sp, $sp, -4
                    '''
            return Node_Return(code=code, type=children[1].type, text="assignment")

    # assignment_expr_with_div: lvalue "/=" expr
    elif parse_tree.data == "assignment_expr_with_div":
        variable_code = children[0].code
        expr_code = children[1].code
        symbol_table.last_scope().pop_variable()
        symbol_table.last_scope().pop_variable()
        symbol_table.last_scope().push_variable(Variable("__IGNORE_assignment_expr_with_div", children[1].type))
        assert children[0].type.inside_type == children[1].type
        if children[1].type.name == "double" or (
                children[1].type.name == "ref" and children[1].type.inside_type == "double"):
            code = f'''{variable_code} {expr_code}
                        \t lw $t0, {children[1].type.size}($sp)
                        \t lw $t1, {children[1].type.size + children[0].type.size}($sp) 
                        \t mtc1 $t0, $f0
                        \t lw $t2, 0($t1)
                        \t mtc1 $t2, $f2
                        \t div.s $f0, $f2, $f0
                        \t mfc1 $t0, $f0
                        \t sw $t0, 0($t1)
                        \t addi $sp, $sp, {children[1].type.size + children[0].type.size}
                        \t sw $t0, 0($sp)
                        \t addi $sp, $sp, -4
                    '''
            return Node_Return(code=code, type=Type("double"), text="assignment")
        else:
            code = f'''{variable_code} {expr_code}
                        \t lw $t0, {children[1].type.size}($sp)
                        \t lw $t1, {children[1].type.size + children[0].type.size}($sp)
                        \t lw $t2, 0($t1)
                        \t div $t0, $t2, $t0
                        \t sw $t0, 0($t1)
                        \t addi $sp, $sp, {children[1].type.size + children[0].type.size}
                        \t sw $t0, 0($sp)
                        \t addi $sp, $sp, -4
                    '''
            return Node_Return(code=code, type=children[1].type, text="assignment")

    # constant: doubleconstant | constant_token | boolconstant
    elif parse_tree.data == "constant":  # TODO only int
        if children[0].type.name == "string":
            return Node_Return(code=children[0].code, type=children[0].type)
        elif children[0].type.name == "double":
            symbol_table.last_scope().push_variable(Variable("__IGNORE_constant_double", Type("double")))
            double_name = "__IGNORE" + get_label()
            code = f''' 
                        .data
                        {double_name}: .float {children[0].text}
                        .text
                        \t la $t0, {double_name}
                        \t lw $t1, 0($t0)
                        \t sw $t1, 0($sp)
                        \t addi $sp, $sp, -4
                    '''
            return Node_Return(code=code, type=children[0].type)
        else:
            symbol_table.last_scope().push_variable(Variable("__IGNORE_constant_NOT_double", children[0].type))
            code = f''' 
                        \t li $t0, {children[0].text}
                        \t sw $t0, 0($sp)
                        \t addi $sp, $sp, -{children[0].type.size}
                    '''
            return Node_Return(code=code, type=children[0].type)

    # doubleconstant
    elif parse_tree.data == "doubleconstant":
        first_part = children[0].text
        second_part = children[1].text.replace("@", "").replace("e", "E")
        if second_part.find("E") == -1:
            return Node_Return(code="", type=Type("double"), text=first_part + "." + second_part)
        else:
            exp = int(second_part[second_part.find("E") + 1:])
            number = (second_part[:second_part.find("E")])
            number = float(first_part + "." + number)
            number = number * (10 ** exp)
            return Node_Return(code="", type=Type("double"), text=str(number))


    # boolconstant: boolconstant_true | boolconstant_false
    elif parse_tree.data == "boolconstant":
        return Node_Return(code="", type=children[0].type, text=children[0].text)

    # math_expr_sum: expr "+" expr
    elif parse_tree.data == "math_expr_sum":
        left_expr_code = children[0].code
        right_expr_code = children[1].code
        symbol_table.last_scope().pop_variable()
        assert children[0].type == children[1].type
        if children[1].type.name == "double" or (
                children[1].type.name == "ref" and children[1].type.inside_type == "double"):
            code = f'''{left_expr_code} {right_expr_code}
                        \t lw $t0, {children[1].type.size}($sp)
                        \t lw $t1, {children[1].type.size + children[0].type.size}($sp)
                        \t mtc1 $t0, $f0
                        \t mtc1 $t1, $f2
                        \t add.s $f0, $f2, $f0
                        \t mfc1 $t0, $f0
                        \t addi $sp, $sp, {children[1].type.size + children[0].type.size}
                        \t sw $t0, 0($sp)
                        \t addi $sp, $sp, -4
                    '''
            return Node_Return(code=code, type=Type("double"), text="math_double")
        elif children[0].type.name == "string" or children[0].type.name == "array":
            code = f'''{left_expr_code} {right_expr_code}
                        \t lw $t0, 4($sp)
                        \t lw $t1, 8($sp)
                        \t addi $sp, $sp, -8
                        #added inputs
                        \t addi $sp, $sp, -8
                        \t sw $t0, 4($sp)
                        \t sw $t1, 8($sp)
                        \t jal math_expr_sum_4
                        \t lw $t0, 4($sp)
                        \t addi $sp, $sp, 12
                        #added inputs
                        \t addi $sp, $sp, 8
                        #expr inputs
                        \t addi $sp, $sp, {children[1].type.size + children[0].type.size}
                        \t sw $t0, 0($sp)
                        \t addi $sp, $sp, -4
                    '''
            return Node_Return(code=code, type=children[0].type.merge_type(children[1].type))
        else:
            code = f'''{left_expr_code} {right_expr_code}
                        \t lw $t0, {children[1].type.size}($sp)
                        \t lw $t1, {children[1].type.size + children[0].type.size}($sp)
                        \t add $t0, $t0, $t1
                        \t addi $sp, $sp, {children[1].type.size + children[0].type.size}
                        \t sw $t0, 0($sp)
                        \t addi $sp, $sp, -4
                    '''
            return Node_Return(code=code, type=Type("int"), text="math_int")

    # math_expr_minus: expr "-" expr
    elif parse_tree.data == "math_expr_minus":
        left_expr_code = children[0].code
        right_expr_code = children[1].code
        symbol_table.last_scope().pop_variable()
        assert children[0].type == children[1].type
        if children[1].type.name == "double" or (
                children[1].type.name == "ref" and children[1].type.inside_type == "double"):
            code = f'''{left_expr_code} {right_expr_code}
                        \t lw $t0, {children[1].type.size}($sp)
                        \t lw $t1, {children[1].type.size + children[0].type.size}($sp)
                        \t mtc1 $t0, $f0
                        \t mtc1 $t1, $f2
                        \t sub.s $f0, $f2, $f0
                        \t mfc1 $t0, $f0
                        \t addi $sp, $sp, {children[1].type.size + children[0].type.size}
                        \t sw $t0, 0($sp)
                        \t addi $sp, $sp, -4
                    '''
            return Node_Return(code=code, type=Type("double"), text="math_double")
        else:
            code = f'''{left_expr_code} {right_expr_code}
                        \t lw $t0, {children[1].type.size}($sp)
                        \t lw $t1, {children[1].type.size + children[0].type.size}($sp)
                        \t sub $t0, $t1, $t0
                        \t addi $sp, $sp, {children[1].type.size + children[0].type.size}
                        \t sw $t0, 0($sp)
                        \t addi $sp, $sp, -4
                    '''
            return Node_Return(code=code, type=Type("int"), text="math_int")

    # math_expr_minus: expr "*" expr
    elif parse_tree.data == "math_expr_mul":
        left_expr_code = children[0].code
        right_expr_code = children[1].code
        symbol_table.last_scope().pop_variable()
        assert children[0].type == children[1].type
        if children[1].type.name == "double" or (
                children[1].type.name == "ref" and children[1].type.inside_type == "double"):
            code = f'''{left_expr_code} {right_expr_code}
                        \t lw $t0, {children[1].type.size}($sp)
                        \t lw $t1, {children[1].type.size + children[0].type.size}($sp)
                        \t mtc1 $t0, $f0
                        \t mtc1 $t1, $f2
                        \t mul.s $f0, $f2, $f0
                        \t mfc1 $t0, $f0
                        \t addi $sp, $sp, {children[1].type.size + children[0].type.size}
                        \t sw $t0, 0($sp)
                        \t addi $sp, $sp, -4
                    '''
            return Node_Return(code=code, type=Type("double"), text="math_double")
        else:
            code = f'''{left_expr_code} {right_expr_code}
                        \tlw $t0, {children[1].type.size}($sp)
                        \tlw $t1, {children[1].type.size + children[0].type.size}($sp)
                        \tmul $t0, $t1, $t0
                        \taddi $sp, $sp, {children[1].type.size + children[0].type.size}
                        \tsw $t0, 0($sp)
                        \taddi $sp, $sp, -4
                    '''
            return Node_Return(code=code, type=Type("int"), text="math_int")

    # math_expr_div: expr "/" expr
    elif parse_tree.data == "math_expr_div":
        left_expr_code = children[0].code
        right_expr_code = children[1].code
        symbol_table.last_scope().pop_variable()
        assert children[0].type == children[1].type
        if children[1].type.name == "double" or (
                children[1].type.name == "ref" and children[1].type.inside_type == "double"):
            code = f'''{left_expr_code} {right_expr_code}
                        \t lw $t0, {children[1].type.size}($sp)
                        \t lw $t1, {children[1].type.size + children[0].type.size}($sp)
                        \t mtc1 $t0, $f0
                        \t mtc1 $t1, $f2
                        \t div.s $f0, $f2, $f0
                        \t mfc1 $t0, $f0
                        \t addi $sp, $sp, {children[1].type.size + children[0].type.size}
                        \t sw $t0, 0($sp)
                        \t addi $sp, $sp, -4
                    '''
            return Node_Return(code=code, type=Type("double"), text="math_double")
        else:
            code = f'''{left_expr_code} {right_expr_code}
                        \t lw $t0, {children[1].type.size}($sp)
                        \t lw $t1, {children[1].type.size + children[0].type.size}($sp)
                        \t div $t0, $t1, $t0
                        \t addi $sp, $sp, {children[1].type.size + children[0].type.size}
                        \t sw $t0, 0($sp)
                        \t addi $sp, $sp, -4
                    '''
            return Node_Return(code=code, type=Type("int"), text="math_int")

    # sign_expr: -expr
    elif parse_tree.data == "sign_expr":
        inside_expr_code = children[0].code
        if children[0].type.name == "double":
            code = f'''{inside_expr_code}
                        \t lw $t0, {children[0].type.size}($sp)
                        \t mtc1 $t0, $f0
                        \t neg.s $f2, $f0
                        \t mfc1 $t0, $f2
                        \t sw $t0, {children[0].type.size}($sp)
                    '''
            return Node_Return(code=code, type=Type("double"), text=children[0].text)
        else:
            code = f'''{inside_expr_code}
                        \t lw $t0, {children[0].type.size}($sp)
                        \t li $t1, -1
                        \t mul $t0, $t1, $t0
                        \t sw $t0, {children[0].type.size}($sp)
                    '''
        assert children[0].type == Type("int") or children[0].type == Type("double")
        return Node_Return(code=code, type=Type("int"), text=children[0].text)


    # math_expr_mod: expr "%" expr
    elif parse_tree.data == "math_expr_mod":
        left_expr_code = children[0].code
        right_expr_code = children[1].code
        symbol_table.last_scope().pop_variable()
        # TODO --------- must handle for double it is not correct too for int
        code = f'''{left_expr_code} {right_expr_code}
                    \t lw $t0, {children[1].type.size}($sp)
                    \t lw $t1, {children[1].type.size + children[0].type.size}($sp)
                    \t div $t3, $t1, $t0
                    \t mul $t3, $t3, $t0
                    \t sub $t0, $t1, $t3
                    \t addi $sp, $sp, {children[1].type.size + children[0].type.size}
                    \t sw $t0, 0($sp)
                    \t addi $sp, $sp, -4
                '''
        assert children[0].type == children[1].type and children[0].type == Type("int")
        return Node_Return(code=code, type=Type("int"), text="math_int")

    # ifstmt: "if""(" expr ")" stmt ("else" stmt)?
    elif parse_tree.data == "ifstmt":
        label = children[1].scope.end_label
        symbol_table.last_scope().pop_variable()
        expr_code = children[0].code
        stmt_if_code = children[1].code
        assert children[0].type == Type("bool")
        if len(children) == 2:
            code = f'''{expr_code}
                        \t lw $t0, {children[0].type.size}($sp)
                        \t sub $t1, $t1, $t1
                        \t beq $t0, $t1, {label}
                        {stmt_if_code} 
                        \t addi $sp, $sp, 4         
                    '''
            return Node_Return(code=code, type=None)
        else:
            stmt_else_code = children[2].code
            label_end = children[2].scope.end_label
            label_else_begin = children[2].scope.begin_label
            code = f'''{expr_code}
                        \t lw $t0, {children[0].type.size}($sp)
                        \t sub $t1, $t1, $t1
                        \t beq $t0, $t1, {label_else_begin}
                        {stmt_if_code}
                        \t j {label_end}
                        {stmt_else_code} 
                        \t addi $sp, $sp, 4        
                    '''
            return Node_Return(code=code, type=None)

    # whilestmt: "while""(" expr ")" stmt
    elif parse_tree.data == "whilestmt":
        symbol_table.last_scope().pop_variable()
        expr_code = children[0].code
        stmt_while_code = children[1].code
        assert children[0].type == Type("bool") or children[0].type == Type("int")
        code = f'''
                    \t {symbol_table.last_scope().begin_label}:
                    \t {symbol_table.last_scope().continue_label}:
                    {expr_code}
                    \t lw $t0, {children[0].type.size}($sp)
                    \t sub $t1, $t1, $t1
                    \t beq $t0, $t1, {symbol_table.last_scope().end_label}
                    {stmt_while_code}
                    \t addi $sp, $sp, 4
                    \t j {symbol_table.last_scope().begin_label}  
                    {symbol_table.last_scope().end_label}:
                    \t addi $sp, $sp, 4
                    \t addi $sp, $sp, {symbol_table.last_scope().size()}
                '''
        symbol_table.pop_scope()
        return Node_Return(code=code, type=None)

    # forstmt: "for" "(" first_forstmt_part ";" expr ";" third_forstmt_part ")" stmt
    elif parse_tree.data == "third_forstmt_part":
        if len(children) > 0:
            symbol_table.last_scope().pop_variable()
            code = f'''
                {children[0].code}
                \t addi $sp, $sp, {children[0].type.size}
            '''
            return Node_Return(code=code, type=None)
        else:
            return Node_Return(code="", type=None)

    elif parse_tree.data == "forstmt":
        first_part_code_type_size = 0
        first_part_code, increment_code = "", ""
        if len(children[0].code):
            first_part_code_type_size = children[0].type.size
            first_part_code += children[0].code
            symbol_table.last_scope().pop_variable()

        condition_child = children[1]
        condition_code = children[1].code
        symbol_table.last_scope().pop_variable()

        if len(children[2].code):
            increment_code += children[2].code

        stmt_for_code = children[3].code

        code = f'''
                    #for first part
                    {first_part_code}
                    #for first part end
                    \t {symbol_table.last_scope().begin_label}:
                    #for condition  start
                    {condition_code}
                    #for condition code end
                    \t lw $t0, {condition_child.type.size}($sp)
                    \t sub $t1, $t1, $t1
                    \t beq $t0, $t1, {symbol_table.last_scope().end_label}
                    #for condition END
                    #for inside code
                    {stmt_for_code}
                    #for inside code END
                    \t {symbol_table.last_scope().continue_label}:
                    {increment_code}
                    \t addi $sp, $sp, 4
                    \t j {symbol_table.last_scope().begin_label}  
                    \t {symbol_table.last_scope().end_label}:
                    \t addi $sp, $sp, {first_part_code_type_size + 4}
                '''
        symbol_table.pop_scope()
        return Node_Return(code=code, type=None)

    # breakstmt: "break" ";"
    elif parse_tree.data == "breakstmt":
        jlabel = None
        pop_size = 0
        for scope in reversed(symbol_table.scope_stack):
            scope: Scope
            if scope.for_scope:
                jlabel = scope.end_label
                break
            else:
                pop_size += scope.size()

        if jlabel is None:
            raise ValueError
        code = f'''
                    \t addi $sp, $sp, {pop_size}
                    \t j {jlabel}
                '''
        return Node_Return(code=code, type=None)

    # continuestmt: "continue" ";"
    elif parse_tree.data == "continuestmt":
        jlabel = None
        pop_size = 0
        for scope in reversed(symbol_table.scope_stack):
            scope: Scope
            if scope.for_scope:
                jlabel = scope.continue_label
                break
            else:
                pop_size += scope.size()

        if jlabel is None:
            raise ValueError
        code = f'''
                    \t addi $sp, $sp, {pop_size}
                    \t j {jlabel}
                '''
        return Node_Return(code=code, type=None)

    # condition_expr_equal: expr "==" expr
    elif parse_tree.data == "condition_expr_equal":
        left_expr_code = children[0].code
        right_expr_code = children[1].code
        symbol_table.last_scope().pop_variable()  # t0 right t1 left
        symbol_table.last_scope().pop_variable()  # t0 right t1 left
        symbol_table.last_scope().push_variable(Variable("__IGNORE_condition_expr_equal_BOOL", Type("bool")))
        assert children[0].type == children[1].type
        if children[1].type.name == "double" or (
                children[1].type.name == "ref" and children[1].type.inside_type == "double"):
            true_label = "__IGONRE" + get_label()
            false_label = "__IGONRE" + get_label()
            code = f'''{left_expr_code} {right_expr_code}
                        \t lw $t0, {children[1].type.size}($sp)
                        \t lw $t1, {children[1].type.size + children[0].type.size}($sp)
                        \t mtc1 $t0, $f0
                        \t mtc1 $t1, $f2
                        \t li $t0, 0
                        \t c.eq.s $f2, $f0
                        \t bc1t {true_label}
                        \t li $t0, 0
                        \t j {false_label}
                        \t {true_label}:
                        \t li $t0, 1
                        \t {false_label}:
                        \t addi $sp, $sp, {children[1].type.size + children[0].type.size}
                        \t sw $t0, 0($sp)
                        \t addi $sp, $sp, -4
                    '''
            return Node_Return(code=code, type=Type("bool"))
        elif children[0].type == Type("string") or children[0].type == Type("array", inside_type="char"):
            code = f'''{left_expr_code} {right_expr_code}
                        #begin string equality check
                        \t lw $t0, 4($sp)
                        \t lw $t1, 8($sp)
                        \t addi $sp, $sp, -8
                        #added inputs
                        \t addi $sp, $sp, -8
                        \t sw $t0, 4($sp)
                        \t sw $t1, 8($sp)
                        \t jal string_equality_check
                        \t lw $t0, 4($sp)
                        #added inputs
                        \t addi $sp, $sp, 8
                        \t addi $sp, $sp, 12
                        #expr inputs
                        \t addi $sp, $sp, {children[1].type.size + children[0].type.size}
                        \t sw $t0, 0($sp)
                        \t addi $sp, $sp, -4
                        #end string equality check
                    '''
            assert children[0].type == children[1].type
            return Node_Return(code=code, type=Type("bool"))
        else:
            # seq $t0, $t0, $t1 ------>>>>> $t0 will be 1 if $t0 and $t1 are equal, and zero otherwise
            code = f'''{left_expr_code} {right_expr_code} 
                        \t lw $t0, {children[1].type.size}($sp)
                        \t lw $t1, {children[1].type.size + children[0].type.size}($sp)
                        \t seq $t0, $t0, $t1
                        \t addi $sp, $sp, {children[1].type.size + children[0].type.size}
                        \t sw $t0, 0($sp)
                        \t addi $sp, $sp, -4
                    '''
        return Node_Return(code=code, type=Type("bool"))

    # condition_expr_equal: expr "<=" expr
    elif parse_tree.data == "condition_expr_less_equal":
        left_expr_code = children[0].code
        right_expr_code = children[1].code
        symbol_table.last_scope().pop_variable()  # t0 right t1 left
        symbol_table.last_scope().pop_variable()  # t0 right t1 left
        symbol_table.last_scope().push_variable(Variable("__IGNORE_condition_expr_less_equal_BOOL", Type("bool")))
        assert children[0].type == children[1].type
        if children[1].type.name == "double" or (
                children[1].type.name == "ref" and children[1].type.inside_type == "double"):
            true_label = "__IGONRE" + get_label()
            false_label = "__IGONRE" + get_label()
            code = f'''{left_expr_code} {right_expr_code}
                        \t lw $t0, {children[1].type.size}($sp)
                        \t lw $t1, {children[1].type.size + children[0].type.size}($sp)
                        \t mtc1 $t0, $f0
                        \t mtc1 $t1, $f2
                        \t li $t0, 0
                        \t c.le.s $f2, $f0
                        \t bc1t {true_label}
                        \t li $t0, 0
                        \t j {false_label}
                        \t {true_label}:
                        \t li $t0, 1
                        \t {false_label}:
                        \t addi $sp, $sp, {children[1].type.size + children[0].type.size}
                        \t sw $t0, 0($sp)
                        \t addi $sp, $sp, -4
                    '''
            return Node_Return(code=code, type=Type("bool"))
        else:
            # sle $t0, $t0, $t1 ------>>>>> $t0 will be 1 if $t0 <= $t1 , and zero otherwise
            code = f'''{left_expr_code} {right_expr_code} 
                        \t lw $t0, {children[1].type.size}($sp)
                        \t lw $t1, {children[1].type.size + children[0].type.size}($sp)
                        \t sle $t0, $t1, $t0
                        \t addi $sp, $sp, {children[1].type.size + children[0].type.size}
                        \t sw $t0, 0($sp)
                        \t addi $sp, $sp, -4
                    '''
        return Node_Return(code=code, type=Type("bool"))

    # condition_expr_less: expr "<" expr
    elif parse_tree.data == "condition_expr_less":
        left_expr_code = children[0].code
        right_expr_code = children[1].code
        symbol_table.last_scope().pop_variable()  # t0 right t1 left
        symbol_table.last_scope().pop_variable()  # t0 right t1 left
        symbol_table.last_scope().push_variable(Variable("__IGNORE_condition_expr_less_BOOL", Type("bool")))
        assert children[0].type == children[1].type
        if children[1].type.name == "double" or (
                children[1].type.name == "ref" and children[1].type.inside_type == "double"):
            true_label = "__IGONRE" + get_label()
            false_label = "__IGONRE" + get_label()
            code = f'''{left_expr_code} {right_expr_code}
                        \t lw $t0, {children[1].type.size}($sp)
                        \t lw $t1, {children[1].type.size + children[0].type.size}($sp)
                        \t mtc1 $t0, $f0
                        \t mtc1 $t1, $f2
                        \t li $t0, 0
                        \t c.lt.s $f2, $f0
                        \t bc1t {true_label}
                        \t li $t0, 0
                        \t j {false_label}
                        \t {true_label}:
                        \t li $t0, 1
                        \t {false_label}:
                        \t addi $sp, $sp, {children[1].type.size + children[0].type.size}
                        \t sw $t0, 0($sp)
                        \t addi $sp, $sp, -4
                    '''
            return Node_Return(code=code, type=Type("bool"))
        else:
            code = f'''{left_expr_code} {right_expr_code} 
                        \t lw $t0, {children[1].type.size}($sp)
                        \t lw $t1, {children[1].type.size + children[0].type.size}($sp)
                        \t slt $t0, $t1, $t0
                        \t addi $sp, $sp, {children[1].type.size + children[0].type.size}
                        \t sw $t0, 0($sp)
                        \t addi $sp, $sp, -4
                    '''
        return Node_Return(code=code, type=Type("bool"))

    # condition_expr_greater: expr ">" expr
    elif parse_tree.data == "condition_expr_greater":
        left_expr_code = children[0].code
        right_expr_code = children[1].code
        symbol_table.last_scope().pop_variable()  # t0 right t1 left
        symbol_table.last_scope().pop_variable()  # t0 right t1 left
        symbol_table.last_scope().push_variable(Variable("__IGNORE_condition_expr_greater_BOOL", Type("bool")))
        assert children[0].type == children[1].type
        if children[1].type.name == "double" or (
                children[1].type.name == "ref" and children[1].type.inside_type == "double"):
            true_label = "__IGONRE" + get_label()
            false_label = "__IGONRE" + get_label()
            code = f'''{left_expr_code} {right_expr_code}
                        \t lw $t0, {children[1].type.size}($sp)
                        \t lw $t1, {children[1].type.size + children[0].type.size}($sp)
                        \t mtc1 $t0, $f0
                        \t mtc1 $t1, $f2
                        \t li $t0, 0
                        \t c.lt.s $f0, $f2
                        \t bc1t {true_label}
                        \t li $t0, 0
                        \t j {false_label}
                        \t {true_label}:
                        \t li $t0, 1
                        \t {false_label}:
                        \t addi $sp, $sp, {children[1].type.size + children[0].type.size}
                        \t sw $t0, 0($sp)
                        \t addi $sp, $sp, -4
                    '''
            return Node_Return(code=code, type=Type("bool"))
        else:
            code = f'''{left_expr_code} {right_expr_code} 
                        \t lw $t0, {children[1].type.size}($sp)
                        \t lw $t1, {children[1].type.size + children[0].type.size}($sp)
                        \t slt $t0, $t0, $t1
                        \t addi $sp, $sp, {children[1].type.size + children[0].type.size}
                        \t sw $t0, 0($sp)
                        \t addi $sp, $sp, -4
                    '''
        return Node_Return(code=code, type=Type("bool"))

    # condition_expr_greater_equal: expr ">=" expr
    elif parse_tree.data == "condition_expr_greater_equal":
        left_expr_code = children[0].code
        right_expr_code = children[1].code
        symbol_table.last_scope().pop_variable()  # t0 right t1 left
        symbol_table.last_scope().pop_variable()  # t0 right t1 left
        symbol_table.last_scope().push_variable(Variable("__IGNORE_condition_expr_greater_equal_BOOL", Type("bool")))
        assert children[0].type == children[1].type
        if children[1].type.name == "double" or (
                children[1].type.name == "ref" and children[1].type.inside_type == "double"):
            true_label = "__IGONRE" + get_label()
            false_label = "__IGONRE" + get_label()
            code = f'''{left_expr_code} {right_expr_code}
                        \t lw $t0, {children[1].type.size}($sp)
                        \t lw $t1, {children[1].type.size + children[0].type.size}($sp)
                        \t mtc1 $t0, $f0
                        \t mtc1 $t1, $f2
                        \t li $t0, 0
                        \t c.le.s $f0, $f2
                        \t bc1t {true_label}
                        \t li $t0, 0
                        \t j {false_label}
                        \t {true_label}:
                        \t li $t0, 1
                        \t {false_label}:
                        \t addi $sp, $sp, {children[1].type.size + children[0].type.size}
                        \t sw $t0, 0($sp)
                        \t addi $sp, $sp, -4
                    '''
            return Node_Return(code=code, type=Type("bool"))
        else:
            code = f'''{left_expr_code} {right_expr_code} 
                        \t lw $t0, {children[1].type.size}($sp)
                        \t lw $t1, {children[1].type.size + children[0].type.size}($sp)
                        \t sle $t0, $t0, $t1
                        \t addi $sp, $sp, {children[1].type.size + children[0].type.size}
                        \t sw $t0, 0($sp)
                        \t addi $sp, $sp, -4
                    '''
        return Node_Return(code=code, type=Type("bool"))

    # condition_expr_not_equal: expr "!=" expr
    elif parse_tree.data == "condition_expr_not_equal":
        left_expr_code = children[0].code
        right_expr_code = children[1].code
        symbol_table.last_scope().pop_variable()
        symbol_table.last_scope().pop_variable()
        symbol_table.last_scope().push_variable(Variable("__IGNORE_condition_expr_not_equal_BOOL", Type("bool")))
        assert children[0].type == children[1].type
        if children[1].type.name == "double" or (
                children[1].type.name == "ref" and children[1].type.inside_type == "double"):
            true_label = "__IGONRE" + get_label()
            false_label = "__IGONRE" + get_label()
            code = f'''{left_expr_code} {right_expr_code}
                        \t lw $t0, {children[1].type.size}($sp)
                        \t lw $t1, {children[1].type.size + children[0].type.size}($sp)
                        \t mtc1 $t0, $f0
                        \t mtc1 $t1, $f2
                        \t li $t0, 0
                        \t c.eq.s $f2, $f0
                        \t bc1t {false_label}
                        \t li $t0, 1
                        \t j {true_label}
                        \t {false_label}:
                        \t li $t0, 0
                        \t {true_label}:
                        \t addi $sp, $sp, {children[1].type.size + children[0].type.size}
                        \t sw $t0, 0($sp)
                        \t addi $sp, $sp, -4
                    '''
            return Node_Return(code=code, type=Type("bool"))
        elif children[0].type == Type("string") or children[0].type == Type("array", inside_type="char"):
            code = f'''{left_expr_code} {right_expr_code}
                        #begin string equality check
                        \t lw $t0, 4($sp)
                        \t lw $t1, 8($sp)
                        \t addi $sp, $sp, -8
                        #added inputs
                        \t addi $sp, $sp, -8
                        \t sw $t0, 4($sp)
                        \t sw $t1, 8($sp)
                        \t jal string_equality_check
                        \t lw $t0, 4($sp)
                        \t li $t1, 1
                        \t sub $t0, $t1, $t0
                        #added inputs
                        \t addi $sp, $sp, 8
                        \t addi $sp, $sp, 12
                        #expr inputs
                        \t addi $sp, $sp, {children[1].type.size + children[0].type.size}
                        \t sw $t0, 0($sp)
                        \t addi $sp, $sp, -4
                        #end string equality check
                    '''
            assert children[0].type == children[1].type
        else:
            code = f'''{left_expr_code} {right_expr_code} 
                        \t lw $t0, {children[1].type.size}($sp)
                        \t lw $t1, {children[1].type.size + children[0].type.size}($sp)
                        \t subu $t2, $t0, $t1
                        \t sltu $t2, $zero, $t2
                        \t addi $sp, $sp, {children[1].type.size + children[0].type.size}
                        \t sw $t2, 0($sp)
                        \t addi $sp, $sp, -4
                    '''
        return Node_Return(code=code, type=Type("bool"))

    # not_expr:  "!" expr
    elif parse_tree.data == "not_expr":
        code = children[0].code
        true_label = get_label()
        false_label = get_label()
        code += f'''
                    \t lw $t0, 4($sp)
                    \t xori $t0, $t0, 1
                    \t sw $t0, 4($sp)
                '''
        assert children[0].type == Type("bool")
        return Node_Return(code=code, type=Type("bool"))

    # printstmt: "Print" "(" expr ("," expr)* ")" ";"
    elif parse_tree.data == "printstmt":
        child_codes_list = []
        sum = 0
        for i in range(len(children)):
            child_codes_list.append(children[i].code)
            sum += children[i].type.size

        code = "".join(child_codes_list)
        org_sum = sum
        for child in children:
            symbol_table.last_scope().pop_variable()
            if child.type.name == "string" or child.type == Type("array", Type("char")):
                label = "PRINT_" + get_label()
                code += f'''
                            #print string start
                            \t lw $t0, {sum}($sp)
                            \t lw $t2, 0($t0)
                            \t addi $t0, $t0, 4
                            \t li $t3, -1
                            \t addi $t2,$t2, -1
                            {label}:
                            \t lb $t1, 0($t0)
                            \t li $v0, 11
                            \t move $a0, $t1
                            \t syscall
                            \t addi $t2,$t2, -1
                            \t addi $t0, $t0, 4
                            \t bne $t2, $t3, {label}
                            #print string end
                        '''
            elif child.type.name == "bool":
                str_label = get_label()
                true_label = get_label()
                false_label = get_label()
                code += f'''
                            \t sub $t0, $t0, $t0
                            \t lw $t1, 4($sp)
                            \t bne $t0, $t1, {true_label}
                            .data
                            \t IGNORE__{false_label}: .asciiz "false"
                            .text
                            \t li $v0, 4
                            \t la $a0, IGNORE__{false_label}
                            \t syscall
                            \t j {false_label}
                            \t {true_label}:
                            .data
                            \t IGNORE__{true_label}: .asciiz "true"
                            .text
                            \t li $v0, 4
                            \t la $a0, IGNORE__{true_label}
                            \t syscall
                            \t {false_label}:
                        '''
            elif child.type.name == "double":
                code += f'''
                            \t lw $t0, {sum}($sp)
                            \t mtc1 $t0, $f0
                            \t li $v0, 2
                            \t sub.s $f2, $f2, $f2
                            \t add.s $f12, $f0, $f2
                            \t syscall
                        '''
            elif child.type.name == "char":
                type_print = 11
            elif child.type.name == "int":
                type_print = 1

            if child.type.name == "char" or child.type.name == "int":
                code += f'''
                            #print int/char start
                            \t lw $t0, {sum}($sp)
                            \t li $v0, {type_print}
                            \t move $a0, $t0
                            \t syscall
                            #print int/char end
                        '''

            sum -= child.type.size

        code += f'''
                    #print endl
                    \taddi $sp, $sp, {org_sum}
                    \tli $a0, 10
                    \tli $v0, 11  
                    \tsyscall
                    #print endl END
                '''
        return Node_Return(code=code, type=None)

    # lvalue_exp: lvalue
    elif parse_tree.data == "lvalue_exp":
        code = f'''{children[0].code}
                    \tlw $t0, 4($sp)
                    \tlw $t1, 0($t0)
                    \tsw $t1, 4($sp)
                '''
        return Node_Return(code=code, type=children[0].type.inside_type)

    # stmt: expr? ";" | ifstmt | whilestmt | whilestmt | forstmt | breakstmt | continuestmt | returnstmt | printstmt | stmtblock  
    elif parse_tree.data == "stmt" or parse_tree.data == "stmtblock":
        code = f'''
                    \t{symbol_table.last_scope().begin_label}:
                '''
        for child in children:
            code += child.code
        code += f'''
                    \t addi $sp, $sp, {symbol_table.last_scope().size()}
                    \t {symbol_table.last_scope().end_label}:
                '''
        symbol_table.pop_scope()
        if len(children) > 0:
            return Node_Return(code=code, type=None, text=children[0].text)

        return Node_Return(code=code, type=None)

    elif parse_tree.data == "mipscode":
        return Node_Return(code=children[0].code)

    # class_function_call: lvalue_exp.ident "(" actuals ")"
    elif parse_tree.data == "class_function_call":
        function_name = children[0].type.class_name + "." + children[1].text.replace("@", "")
        method: Method = symbol_table.get_method(function_name, [children[0].type] + children[2].type)
        for var in method.input_variables:
            symbol_table.last_scope().pop_variable()
        symbol_table.last_scope().pop_variable()
        symbol_table.last_scope().pop_variable()

        code = f'''
                    #load GSA
                    \tlw $t0, {symbol_table.get_address_diff("$GSA")}($sp)
                    \taddi $sp, $sp, -{Type("int").size}
                    \tsw $t0, 0($sp)
                    \taddi $sp, $sp, -{Type("int").size}
                '''
        for child in children:
            code += child.code

        if method.output_type.size != 0:
            code += f'''
                        \t jal {function_name}
                        \t lw $t0, {method.output_type.size}($sp)
                        \t addi $sp, $sp, {method.output_type.size}
                        \t addi $sp, $sp, {method.get_method_inputs_size() + Type("int").size + Type("int").size}
                        \t sw $t0, 0($sp)
                        \t addi $sp, $sp, -{method.output_type.size}
                    '''
        else:
            code += f'''
                        \t jal {function_name}
                        \t addi $sp, $sp, {method.get_method_inputs_size() + Type("int").size + Type("int").size}
                    '''
        # print("&" * 40)
        # for var in symbol_table.last_scope().variables:
        #     print(var)
        # print("*" * 40)
        symbol_table.last_scope().push_variable(Variable("__IGNORE_function_output", method.output_type))
        return Node_Return(code=code, type=method.output_type)


    # normal_function_call: ident "(" actuals ")"
    elif parse_tree.data == "normal_function_call":
        function_name = children[0].text.replace("@", "")
        method: Method = symbol_table.get_method(function_name, children[1].type)
        for var in method.input_variables:
            symbol_table.last_scope().pop_variable()
        symbol_table.last_scope().pop_variable()
        symbol_table.last_scope().pop_variable()

        code = f'''
                    #load GSA
                    \tlw $t0, {symbol_table.get_address_diff("$GSA")}($sp)
                    \taddi $sp, $sp, -{Type("int").size}
                    \tsw $t0, 0($sp)
                    \taddi $sp, $sp, -{Type("int").size}
                '''
        for child in children:
            code += child.code

        if method.output_type.size != 0:
            code += f'''
                        \t jal {function_name}
                        \t lw $t0, {method.output_type.size}($sp)
                        \t addi $sp, $sp, {method.output_type.size}
                        \t addi $sp, $sp, {method.get_method_inputs_size() + Type("int").size + Type("int").size}
                        \t sw $t0, 0($sp)
                        \t addi $sp, $sp, -{method.output_type.size}
                    '''
        else:
            code += f'''
                        \t jal {function_name}
                        \t addi $sp, $sp, {method.get_method_inputs_size() + Type("int").size + Type("int").size}
                    '''
        # print("&" * 40)
        # for var in symbol_table.last_scope().variables:
        #     print(var)
        # print("*" * 40)
        symbol_table.last_scope().push_variable(Variable("__IGNORE_function_output", method.output_type))
        return Node_Return(code=code, type=method.output_type)

    # function_decl: type ident "(" formals ")" stmtblock | /void/ ident "(" formals ")" stmtblock
    elif parse_tree.data == "function_decl":
        function_name = parse_tree.method.name
        stmtblock_code = children[3].code
        save_ra = f'''sw $ra {symbol_table.get_address_diff("$RA")}($sp)'''

        code = f'''
                    {function_name}:
                    {save_ra}
                    {stmtblock_code}
                '''
        code += f'''
                    \t lw $t1, {symbol_table.get_address_diff("$RA")}($sp)
                '''
        pop_size = 0
        for scope in reversed(symbol_table.scope_stack):
            scope: Scope
            if scope.method_scope:
                break
            else:
                pop_size += scope.size()
        code += f'''
                    \t addi $sp, $sp, {pop_size}
                    \t addi $sp, $sp, -{parse_tree.method.output_type.size}
                    \t jr $t1
                '''

        symbol_table.pop_scope()
        return Node_Return(code=code, type=None)

    elif parse_tree.data == "class_decl":
        code = f'''
        #class start'''
        for i, child in enumerate(children):
            if parse_tree.children[i].data == "field" and parse_tree.children[i].children[1].data == "function_decl":
                code += child.code
        code += f'''
        #class end
        '''
        symbol_table.pop_scope()
        return Node_Return(code=code, type=None)

    # formals: variable ("," variable)+ |  variable | null
    elif parse_tree.data == "formals":
        type_list = []
        variable_count = 0 if parse_tree.children[0].data == "null" else len(children)
        for i in range(variable_count):
            type_list.append(symbol_table.last_scope().variables[i])

        return Node_Return(code=None, type=type_list)

    # returnstmt: "return" expr? ";"
    elif parse_tree.data == "returnstmt":
        pop_size = 0
        function_scope = None
        for scope in reversed(symbol_table.scope_stack):
            scope: Scope
            if scope.method_scope:
                function_scope = scope
                break
            else:
                pop_size += scope.size()

        if function_scope is None:
            raise ValueError

        # for return; without any parameter
        if len(children) == 0:
            code = f'''
                        \t lw $t1, {symbol_table.get_address_diff("$RA")}($sp)
                        \t addi $sp, $sp, {pop_size}
                        \t jr $t1
                    '''
        else:
            code = f'''{children[0].code}
                        \t lw $t1, {symbol_table.get_address_diff("$RA")}($sp)
                        \t lw $t0, {children[0].type.size}($sp)
                        \t addi $sp, $sp, {pop_size}
                        \t sw $t0, 0($sp)
                        \t addi $sp, $sp, -{children[0].type.size}
                        \t jr $t1
                    '''
            assert children[0].type == function_scope.method.output_type
        return Node_Return(code=code, type=None)

    elif parse_tree.data == "bool_math_expr_and":
        left_expr_code = children[0].code
        right_expr_code = children[1].code
        symbol_table.last_scope().pop_variable()
        code = f'''{left_expr_code} {right_expr_code}
                    \t lw $t0, {children[1].type.size}($sp)
                    \t lw $t1, {children[1].type.size + children[0].type.size}($sp)
                    \t and $t0, $t1, $t0
                    \t addi $sp, $sp, {children[1].type.size + children[0].type.size}
                    \t sw $t0, 0($sp)
                    \t addi $sp, $sp, -4
                '''
        return Node_Return(code=code, type=children[0].type.merge_type(children[1].type, ["bool"]))

    elif parse_tree.data == "bool_math_expr_or":
        left_expr_code = children[0].code
        right_expr_code = children[1].code
        symbol_table.last_scope().pop_variable()
        code = f'''{left_expr_code} {right_expr_code}
                    \t lw $t0, {children[1].type.size}($sp)
                    \t lw $t1, {children[1].type.size + children[0].type.size}($sp)
                    \t or $t0, $t1, $t0
                    \t addi $sp, $sp, {children[1].type.size + children[0].type.size}
                    \t sw $t0, 0($sp)
                    \t addi $sp, $sp, -4
                '''
        return Node_Return(code=code, type=children[0].type.merge_type(children[1].type, ["bool"]))

    # actuals: expr ("," expr)* | null
    elif parse_tree.data == "actuals":
        if len(children) == 1 and parse_tree.children[0].data == "null":
            return Node_Return(code="", type=[])
        code = ''
        for child in children:
            if child.code is not None:
                code += child.code

        return Node_Return(code=code, type=[children[i].type for i in range(len(children))])
    elif parse_tree.data == "program":
        code = f'''{parse_tree.code}
        \t addi $t0, $sp, 0
        \t addi $sp, $sp, -4
        \t sw $t0, 0($sp)
        \t addi $sp, $sp, -4
        jal main
        j ENDPROGRAM
        '''
        for child in children:
            if child.code is not None:
                code += child.code
            else:
                code += child.text
        code += '''
        ENDPROGRAM:
        '''
        return Node_Return(code=code, type=children[0].type, text=children[0].text)
    elif parse_tree.data == "call":
        return Node_Return(code=children[0].code, type=children[0].type)
    else:
        code = ''
        for child in children:
            if child.code is not None:
                code += child.code
            else:
                code += child.text
        return Node_Return(code=code, type=children[0].type if len(children) > 0 else Type(),
                           text=children[0].text if len(children) > 0 else None)  # TODO: not good!


def get_code_assignment_expr_double(children, type, variable_code, expr_code, command):
    code = f'''{variable_code} {expr_code}
                    \t lw $t0, {children[1].type.size}($sp)
                    \t lw $t1, {children[1].type.size + children[0].type.size}($sp)
                '''
    if type == "expr_is_ref":
        code += f'''
                    \t lw $t3, 0($t0)
                    \t lwc1 $f0, 0($t3)
                '''
    else:
        code += f'''
                    \t lwc1 $f0, 0($t0)
                '''
    code += f'''
                    \t lw $t2, 0($t1)
                    \t lwc1 $f2, 0($t0)
                    \t {command} $f0, $f2, $f0
                    \t swc1 $f0, 0($t2)
                    \t addi $sp, $sp, {children[1].type.size + children[0].type.size}
                    \t sw $t2, 0($sp)
                    \t addi $sp, $sp, -4
                '''
    return code


def get_code_math_expr_double(children, type1, type2, left_expr_code, right_expr_code, command):
    double_name = "__IGNORE" + get_label()
    # create variable, push result in this variable, reference is at the top of the stack

    code = f'''{left_expr_code} {right_expr_code}
                    \t lw $t0, {children[1].type.size}($sp)
                    \t lw $t1, {children[1].type.size + children[0].type.size}($sp)
                '''
    if type1 == "expr_is_ref":
        code += f'''
                    \t lw $t3, 0($t0)
                    \t lwc1 $f0, 0($t3)
                '''
    else:
        code += f'''
                    \t lwc1 $f0, 0($t0)
                '''
    if type2 == "expr_is_ref":
        code += f'''
                    \t lw $t4, 0($t1)
                    \t lwc1 $f2, 0($t4)
                '''
    else:
        code += f'''
                    \t lwc1 $f2, 0($t1)
                '''
    code += f'''
                    \t {command} $f0, $f2, $f0
                    \t addi $sp, $sp, {children[1].type.size + children[0].type.size}
                    .data
                    {double_name}: .float 0.0
                    .text
                    \t la $t0, {double_name}
                    \t swc1 $f0, 0($t0)
                    \t sw $t0, 0($sp)
                    \t addi $sp, $sp, -4
                '''
    return code


def get_code_condition_expr_double(children, type1, type2, left_expr_code, right_expr_code, command, reg1, reg2):
    true_label = "__IGONRE" + get_label()
    false_label = "__IGONRE" + get_label()

    code = f'''{left_expr_code} {right_expr_code}
                    \t lw $t0, {children[1].type.size}($sp)
                    \t lw $t1, {children[1].type.size + children[0].type.size}($sp)
                '''
    if type1 == "expr_is_ref":
        code += f'''
                    \t lw $t3, 0($t0)
                    \t lwc1 $f0, 0($t3)
                '''
    else:
        code += f'''
                    \t lwc1 $f0, 0($t0)
                '''
    if type2 == "expr_is_ref":
        code += f'''
                    \t lw $t4, 0($t1)
                    \t lwc1 $f2, 0($t4)
                '''
    else:
        code += f'''
                    \t lwc1 $f2, 0($t1)
                '''
    code += f'''
                    \t li $t0, 0
                    \t {command} {reg1}, {reg2}
                    \t bc1t {true_label}
                    \t li $t0, 0
                    \t j {false_label}
                    \t {true_label}:
                    \t li $t0, 1
                    \t {false_label}:
                    \t addi $sp, $sp, {children[1].type.size + children[0].type.size}
                    \t sw $t0, 0($sp)
                    \t addi $sp, $sp, -4
                '''
    return code


all_node = '''
    program 
    macro 
    decl 
    variable_decl 
    variable 
    type
    function_decl
    formals 
    class_decl 
    field 
    access_mode 
    interface_decl
    prototype 
    stmtblock
    stmt
    ifstmt
    whilestmt
    forstmt 
    returnstmt 
    breakstmt 
    continuestmt 
    printstmt 
    expr     
    lvalue_exp
    this_expr 
    new_expr
    new_array_expr 
    assignment_expr 
    not_expr 
    sign_expr
    condition_expr 
    bool_math_expr 
    type_change_expr
    input_expr
    
    assignment_expr_empty 
    assignment_expr_with_plus 
    assignment_expr_with_mul 
    assignment_expr_with_div 
    assignment_expr_with_min

    math_expr_minus 
    math_expr_sum 
    math_expr_mul 
    math_expr_div 
    math_expr_mod 

    condition_expr_less 
    condition_expr_less_equal 
    condition_expr_greater 
    condition_expr_greater_equal 
    condition_expr_equal
    condition_expr_not_equal 

    bool_math_expr_and 
    bool_math_expr_or 

    type_change_expr_itod 
    type_change_expr_dtoi 
    type_change_expr_itob 
    type_change_expr_btoi 

    input_expr_readint 
    input_expr_readline 
    
    lvalue 
    class_val 
    array_val 
    
    call  
    class_function_call 
    normal_function_call 
    
    actuals 
    constant 
    constant_token 
    null
    ident 
    doubleconstant 
    boolconstant 
    boolconstant_true 
    boolconstant_false 
'''
