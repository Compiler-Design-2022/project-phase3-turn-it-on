from SymbolTable import SymbolTable, Scope, Variable, Type, get_label
import lark
import copy


class Node_Return:
    def __init__(self, code=None, type=None, scope=None, text=None):
        self.code = code
        self.type = type
        self.scope = scope
        self.text = text


def cgen_token(token: lark.Token, symboltable: SymbolTable):
    return Node_Return(text=token.value, type=Type())


def cgen(parse_tree, symbol_table: SymbolTable):
    if parse_tree.__class__ is lark.Token:
        return cgen_token(parse_tree, symbol_table)
    
    print("^" * 60, parse_tree.data, parse_tree._meta)
    before_enter(parse_tree, symbol_table)
    children_return = []
    for child in parse_tree.children:
        child_return = cgen(child, symbol_table)
        children_return.append(child_return)

    scope = symbol_table.last_scope()
    print(len(symbol_table.scope_stack))
    gen: Node_Return = after_enter(parse_tree, symbol_table, children_return)
    gen.scope = scope
    return gen


def before_enter(parse_tree, symbol_table):
    if parse_tree.data == "stmt":
        new_scope = Scope()
        symbol_table.push_scope(new_scope)
    elif parse_tree.data == "whilestmt":
        new_scope = Scope(for_scope=True)
        symbol_table.push_scope(new_scope)
    elif parse_tree.data == "forstmt":
        new_scope = Scope(for_scope=True)
        symbol_table.push_scope(new_scope)
    return


def after_enter(parse_tree, symbol_table, children):
    """ variable: type ident """
    if parse_tree.data == "type":
        if children[0].text == None: 
            return children[0]
        return Node_Return(code="", type=Type(children[0].text))
    elif parse_tree.data == "ident":
        return Node_Return(code="", type=None, text=children[0].text)
    elif parse_tree.data == "null":
        return Node_Return(code="", type=None, text="")
    elif parse_tree.data == "constant_token":
        return Node_Return(code="", type=children[0].type, text=children[0].text)
    elif parse_tree.data == "variable":
        variable = Variable(children[1].text, children[0].type)
        symbol_table.last_scope().push_variable(variable)
        
        # init value is 0 for int #TODO  string double ... 
        code = f'''
            sub $t1, $t1, $t1
            sw $t0, 0($sp)
            addi $sp, $sp, -{variable.type.size}
        '''
        return Node_Return(code=code, type=None)

    # lvalue: ident |  class_val | array_val
    if parse_tree.data == "lvalue":  # DOTO array, class
        if parse_tree.children[0].data != "ident":
            return children[0]
        diff = symbol_table.get_address_diff(children[0].text)
        var = symbol_table.get_variable(children[0].text)
        symbol_table.last_scope().push_variable(Variable("__IGNORE", var.type))
        code = f'''
        \taddi $t0, $sp, {diff}
        \tsw $t0, 0($sp)
        \taddi $sp, $sp, -4
        '''
        return Node_Return(code=code, type=Type("ref", inside_type=var.type))

    # new_array_expr: "NewArray" "(" expr "," type ")"
    elif parse_tree.data == "new_array_expr": #TODO differrent type different code 
        expr_code = children[0].code

        code = f'''
            \t{expr_code}
            \t lw $t0, {children[0].type.size}($sp)
            \t sub $t1, $t1, $t1 
            \t addi $t1, $t1, {children[1].type.size}
            \t mul $t0, $t0, $t1
            \t move $a0, $t0
            \t li $v0, 9 
            \t syscall
            \t sw $v0, {children[0].type.size}($sp)

        '''
        return Node_Return(code=code, type=Type("ref", inside_type=children[1].type))

    # array_val: expr "[" expr "]"
    elif parse_tree.data == "array_val": 
        left_expr_code = children[0].code
        right_expr_code = children[1].code
        symbol_table.last_scope().pop_variable()
        code = f'''{left_expr_code} {right_expr_code}
                    \tlw $t0, {children[1].type.size}($sp)
                    \tlw $t1, {children[1].type.size + children[0].type.size}($sp)
                    \tli $t2, {children[0].type.size}
                    \tmul $t0, $t0, $t2 
                    \tadd $t0, $t0, $t1
                    \taddi $sp, $sp, {children[1].type.size + children[0].type.size}
                    \tsw $t0, 0($sp)
                    \taddi $sp, $sp, -4
                '''
        return Node_Return(code=code, type=children[0].type)

    # assignment_expr_empty: lvalue "=" expr
    elif parse_tree.data == "assignment_expr_empty":
        variable_code = children[0].code
        expr_code = children[1].code
        symbol_table.last_scope().pop_variable()
        symbol_table.last_scope().pop_variable()
        code = f'''{variable_code} {expr_code}
            \tlw $t0, {children[1].type.size}($sp)
            \tlw $t1, {children[1].type.size + children[0].type.size}($sp)
            \tsw $t0, 0($t1)
            \taddi $sp, $sp, {children[1].type.size + children[0].type.size}
        '''
        return Node_Return(code=code, type=children[1].type, text="assignment_expr_empty")

    # assignment_expr_with_plus: lvalue "+=" expr
    elif parse_tree.data == "assignment_expr_with_plus":
        variable_code = children[0].code
        expr_code = children[1].code
        symbol_table.last_scope().pop_variable()
        symbol_table.last_scope().pop_variable()
        code = f'''{variable_code} {expr_code}
            \tlw $t0, {children[1].type.size}($sp)
            \tlw $t1, {children[1].type.size + children[0].type.size}($sp)
            \tlw $t2, 0($t1)
            \tadd $t0, $t0, $t2
            \tsw $t0, 0($t1)
            \taddi $sp, $sp, {children[1].type.size + children[0].type.size}
        '''
        return Node_Return(code=code, type=children[0].type.merge_type(children[1].type))

    # assignment_expr_with_min: lvalue "-=" expr
    elif parse_tree.data == "assignment_expr_with_min":
        variable_code = children[0].code
        expr_code = children[1].code
        symbol_table.last_scope().pop_variable()
        symbol_table.last_scope().pop_variable()
        code = f'''{variable_code} {expr_code}
            \tlw $t0, {children[1].type.size}($sp)
            \tlw $t1, {children[1].type.size + children[0].type.size}($sp)
            \tlw $t2, 0($t1)
            \tsub $t0, $t2, $t0
            \tsw $t0, 0($t1)
            \taddi $sp, $sp, {children[1].type.size + children[0].type.size}
        '''
        return Node_Return(code=code, type=children[0].type.merge_type(children[1].type))

    # assignment_expr_with_mul: lvalue "*=" expr
    elif parse_tree.data == "assignment_expr_with_mul":
        variable_code = children[0].code
        expr_code = children[1].code
        symbol_table.last_scope().pop_variable()
        symbol_table.last_scope().pop_variable()
        code = f'''{variable_code} {expr_code}
            \tlw $t0, {children[1].type.size}($sp)
            \tlw $t1, {children[1].type.size + children[0].type.size}($sp)
            \tlw $t2, 0($t1)
            \tmul $t0, $t2, $t0
            \tsw $t0, 0($t1)
            \taddi $sp, $sp, {children[1].type.size + children[0].type.size}
        '''
        return Node_Return(code=code, type=children[0].type.merge_type(children[1].type))

    # assignment_expr_with_div: lvalue "/=" expr
    elif parse_tree.data == "assignment_expr_with_div":
        variable_code = children[0].code
        expr_code = children[1].code
        symbol_table.last_scope().pop_variable()
        symbol_table.last_scope().pop_variable()
        code = f'''{variable_code} {expr_code}
            \tlw $t0, {children[1].type.size}($sp)
            \tlw $t1, {children[1].type.size + children[0].type.size}($sp)
            \tlw $t2, 0($t1)
            \tdiv $t0, $t2, $t0
            \tsw $t0, 0($t1)
            \taddi $sp, $sp, {children[1].type.size + children[0].type.size}
        '''
        return Node_Return(code=code, type=children[0].type.merge_type(children[1].type))

    # constant: doubleconstant | constant_token | boolconstant
    elif parse_tree.data == "constant":  # TODO only int
        symbol_table.last_scope().push_variable(Variable("__IGNORE", children[0].type))
        code = f''' \tsub $t0, $t0, $t0
                    \taddi $t0, $t0, {children[0].text}
                    \tsw $t0, 0($sp)
                    \taddi $sp, $sp, -{children[0].type.size}
                '''
        return Node_Return(code=code, type=children[0].type)

    # math_expr_sum: expr "+" expr
    elif parse_tree.data == "math_expr_sum":
        left_expr_code = children[0].code
        right_expr_code = children[1].code
        symbol_table.last_scope().pop_variable()
        code = f'''{left_expr_code} {right_expr_code}
                    \tlw $t0, {children[1].type.size}($sp)
                    \tlw $t1, {children[1].type.size + children[0].type.size}($sp)
                    \tadd $t0, $t0, $t1
                    \taddi $sp, $sp, {children[1].type.size + children[0].type.size}
                    \tsw $t0, 0($sp)
                    \taddi $sp, $sp, -4
                '''
        return Node_Return(code=code, type=children[0].type.merge_type(children[1].type))

    # math_expr_minus: expr "-" expr
    elif parse_tree.data == "math_expr_minus":
        left_expr_code = children[0].code
        right_expr_code = children[1].code
        symbol_table.last_scope().pop_variable()
        code = f'''{left_expr_code} {right_expr_code}
                    \tlw $t0, {children[1].type.size}($sp)
                    \tlw $t1, {children[1].type.size + children[0].type.size}($sp)
                    \tsub $t0, $t1, $t0
                    \taddi $sp, $sp, {children[1].type.size + children[0].type.size}
                    \tsw $t0, 0($sp)
                    \taddi $sp, $sp, -4
                '''
        return Node_Return(code=code, type=children[0].type.merge_type(children[1].type))


    # ifstmt: "if""(" expr ")" stmt ("else" stmt)?
    elif parse_tree.data == "ifstmt":
        label = children[1].scope.end_label
        symbol_table.last_scope().pop_variable()
        expr_code = children[0].code
        stmt_if_code = children[1].code
        if len(children) == 2:
            code = f'''{expr_code}
                \tlw $t0, {children[0].type.size}($sp)
                \tsub $t1, $t1, $t1
                \tbeq $t0, $t1, {label}
                {stmt_if_code} 
                \taddi $sp, $sp, 4         
            '''
            return Node_Return(code=code, type=None)
        else:
            stmt_else_code = children[2].code
            label_end = children[2].scope.end_label
            label_else_begin = children[2].scope.begin_label
            code = f'''{expr_code}
                            \tlw $t0, {children[0].type.size}($sp)
                            
                            \tsub $t1, $t1, $t1
                            \tbeq $t0, $t1, {label_else_begin}
                            {stmt_if_code}
                            \tj {label_end}
                            {stmt_else_code} 
                            \taddi $sp, $sp, 4        
                        '''
            return Node_Return(code=code, type=None)

    # whilestmt: "while""(" expr ")" stmt
    elif parse_tree.data == "whilestmt":
        symbol_table.last_scope().pop_variable()
        expr_code = children[0].code
        stmt_while_code = children[1].code

        code = f'''
            \t{symbol_table.last_scope().begin_label}:
            {expr_code}
            \tlw $t0, {children[0].type.size}($sp)
            \tsub $t1, $t1, $t1
            \tbeq $t0, $t1, {symbol_table.last_scope().end_label}
            {stmt_while_code}
            \taddi $sp, $sp, 4
            \tj {symbol_table.last_scope().begin_label}  
            \t{symbol_table.last_scope().end_label}:
            \taddi $sp, $sp, 4
            \taddi $sp, $sp, {symbol_table.last_scope().size()}
        '''
        symbol_table.pop_scope()
        return Node_Return(code=code, type=None)

    # forstmt: "for" "(" first_forstmt_part ";" expr ";" third_forstmt_part ")" stmt
    elif parse_tree.data == "forstmt":
        first_part_code_type_size, third_part_code_type_size, id = 0, 0, 0
        first_part_code, increment_code = "", ""
        if parse_tree.children[id].data == "first_forstmt_part":
            #symbol_table.last_scope().pop_variable()
            first_part_code_type_size = children[id].type.size
            first_part_code += children[id].code
            id += 1

        condition_child=children[id]
        condition_code = children[id].code
        symbol_table.last_scope().pop_variable()
        id += 1

        if parse_tree.children[id].data == "third_forstmt_part":
            #symbol_table.last_scope().pop_variable()
            third_part_code_type_size += children[id].type.size
            increment_code += children[id].code
            id += 1

        stmt_for_code = children[id].code

        # remove \taddi $sp, $sp, {first_part_code_type_size} from second line
        # remove \taddi $sp, $sp, 4 from line below stmt_for_code
        code = f'''
            {first_part_code}
            
            \t{symbol_table.last_scope().begin_label}:
            {condition_code}
            \tlw $t0, {condition_child.type.size}($sp)
            \tsub $t1, $t1, $t1
            \tbeq $t0, $t1, {symbol_table.last_scope().end_label}
            {stmt_for_code}
            
            {increment_code}
            \taddi $sp, $sp, {third_part_code_type_size}
            \tj {symbol_table.last_scope().begin_label}  
            \t{symbol_table.last_scope().end_label}:
            \taddi $sp, $sp, 4
            \taddi $sp, $sp, {symbol_table.last_scope().size()}
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
            \taddi $sp, $sp, {pop_size}
            \tj {jlabel}
                            '''
        return Node_Return(code=code, type=None)

    # continuestmt: "continue" ";"
    elif parse_tree.data == "continuestmt":
        jlabel = None
        pop_size = 0
        for scope in reversed(symbol_table.scope_stack):
            scope: Scope
            if scope.for_scope:
                jlabel = scope.begin_label
                break
            else:
                pop_size += scope.size()

        if jlabel is None:
            raise ValueError
        code = f'''
            \taddi $sp, $sp, {pop_size}
            \tj {jlabel}
                            '''
        return Node_Return(code=code, type=None)

    # condition_expr_equal: expr "==" expr
    elif parse_tree.data == "condition_expr_equal":
        left_expr_code = children[0].code
        right_expr_code = children[1].code
        symbol_table.last_scope().pop_variable()  # t0 right t1 left
        # seq $t0, $t0, $t1 ------>>>>> $t0 will be 1 if $t0 and $t1 are equal, and zero otherwise
        code = f'''{left_expr_code} {right_expr_code} 
                    \tlw $t0, {children[1].type.size}($sp)
                    \tlw $t1, {children[1].type.size + children[0].type.size}($sp)
                    \tseq $t0, $t0, $t1
                    \taddi $sp, $sp, {children[1].type.size + children[0].type.size}
                    \tsw $t0, 0($sp)
                    \taddi $sp, $sp, -4
                '''
        return Node_Return(code=code, type=Type("bool"))

    # condition_expr_less: expr "<" expr
    elif parse_tree.data == "condition_expr_less":
        left_expr_code = children[0].code
        right_expr_code = children[1].code
        symbol_table.last_scope().pop_variable()  # t0 right t1 left
        code = f'''{left_expr_code} {right_expr_code} 
                    \tlw $t0, {children[1].type.size}($sp)
                    \tlw $t1, {children[1].type.size + children[0].type.size}($sp)
                    \tslt $t0, $t1, $t0
                    \taddi $sp, $sp, {children[1].type.size + children[0].type.size}
                    \tsw $t0, 0($sp)
                    \taddi $sp, $sp, -4
                '''
        return Node_Return(code=code, type=Type("bool"))

    # condition_expr_greater: expr ">" expr
    elif parse_tree.data == "condition_expr_greater":
        left_expr_code = children[0].code
        right_expr_code = children[1].code
        symbol_table.last_scope().pop_variable()  # t0 right t1 left
        code = f'''{left_expr_code} {right_expr_code} 
                    \tlw $t0, {children[1].type.size}($sp)
                    \tlw $t1, {children[1].type.size + children[0].type.size}($sp)
                    \tslt $t0, $t0, $t1
                    \taddi $sp, $sp, {children[1].type.size + children[0].type.size}
                    \tsw $t0, 0($sp)
                    \taddi $sp, $sp, -4
                '''
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
        for child in reversed(children):
            if len(symbol_table.last_scope().variables) > 0:
                symbol_table.last_scope().pop_variable()
            code += f'''
            \t lw $t0, {sum}($sp)
            \t li $v0, 1
            \t move $a0, $t0
            \t syscall
            \tli $a0, 32
            \tli $v0, 11  
            \tsyscall
            '''
            sum -= child.type.size

        # org_sum must be 0 if expr in printstmt rule is assignment_expr
        if len(children) == 1 and children[0].text == "assignment_expr_empty":
            org_sum = 0;
        code += f'''
            \taddi $sp, $sp, {org_sum}
            \tli $a0, 10
            \tli $v0, 11  
            \tsyscall
        '''
        return Node_Return(code=code, type=None)

    # math_expr_minus: expr "*" expr
    elif parse_tree.data == "math_expr_mul":
        left_expr_code = children[0].code
        right_expr_code = children[1].code
        symbol_table.last_scope().pop_variable()
        code = f'''{left_expr_code} {right_expr_code}
                    \tlw $t0, {children[1].type.size}($sp)
                    \tlw $t1, {children[1].type.size + children[0].type.size}($sp)
                    \tmul $t0, $t1, $t0
                    \taddi $sp, $sp, {children[1].type.size + children[0].type.size}
                    \tsw $t0, 0($sp)
                    \taddi $sp, $sp, -4
                '''
        return Node_Return(code=code, type=children[0].type.merge_type(children[1].type))

    # math_expr_div: expr "/" expr
    elif parse_tree.data == "math_expr_div":
        left_expr_code = children[0].code
        right_expr_code = children[1].code
        symbol_table.last_scope().pop_variable()
        code = f'''{left_expr_code} {right_expr_code}
                    \tlw $t0, {children[1].type.size}($sp)
                    \tlw $t1, {children[1].type.size + children[0].type.size}($sp)
                    \tdiv $t0, $t1, $t0
                    \taddi $sp, $sp, {children[1].type.size + children[0].type.size}
                    \tsw $t0, 0($sp)
                    \taddi $sp, $sp, -4
                '''
        return Node_Return(code=code, type=children[0].type.merge_type(children[1].type))

    # math_expr_mod: expr "%" expr
    elif parse_tree.data == "math_expr_div":  # TODO: previous if is the same thing!
        left_expr_code = children[0].code
        right_expr_code = children[1].code
        symbol_table.last_scope().pop_variable()
        code = f'''{left_expr_code} {right_expr_code}
                    \tlw $t0, {children[1].type.size}($sp)
                    \tlw $t1, {children[1].type.size + children[0].type.size}($sp)
                    \tdivu $t1, $t0
                    \tmfhi $t0       # temp for the mod
                    \taddi $sp, $sp, {children[1].type.size + children[0].type.size}
                    \tsw $t0, 0($sp)
                    \taddi $sp, $sp, -4
                '''
        return Node_Return(code=code, type=Type())


    # lvalue_exp: lvalue
    elif parse_tree.data == "lvalue_exp":
        code = f'''{children[0].code}
                            \tlw $t0, 4($sp)
                            \tlw $t1, 0($t0)
                            \tsw $t1, 4($sp)
                        '''
        return Node_Return(code=code, type=children[0].type.inside_type)

    # stmt: expr? ";" | ifstmt | whilestmt | whilestmt | forstmt | breakstmt | continuestmt | returnstmt | printstmt | stmtblock  
    elif parse_tree.data == "stmt":
        code = f'''
        \t{symbol_table.last_scope().begin_label}:
        '''

        for child in children:
            code += child.code
        code += f'''
        \taddi $sp, $sp, {symbol_table.last_scope().size()}
        \t{symbol_table.last_scope().end_label}:
        '''
        symbol_table.pop_scope()
        return Node_Return(code=code, type=None, text=children[0].text)

    # stmtblock: "{" variable_decl* stmt* "}" 
    elif parse_tree.data == "stmtblock":
        code = ""
        for child in children:
            code += child.code
        return Node_Return(code=code, type=None)
    elif parse_tree.data == "expr" or parse_tree.data == "assignment_expr":
        code = ''
        for child in children:
            if child.code is not None:
                code += child.code
            else:
                code += child.text
        return Node_Return(code=code, type=Type(), text=children[0].text)  # TODO: not good!
    else:
        code = ''
        for child in children:
            if child.code is not None:
                code += child.code
            else:
                code += child.text
        return Node_Return(code=code, type=Type())  # TODO: not good!


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
