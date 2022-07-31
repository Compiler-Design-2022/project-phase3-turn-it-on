from SymbolTable import SymbolTable, Scope, Variable, Type, get_label
import lark


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

    mips_code, result_type = after_enter(parse_tree, symbol_table, children_return)
    return mips_code, result_type


def before_enter(parse_tree, symbol_table):
    if parse_tree.data == "stmtblock":
        symbol_table.push_scope(Scope())
    return


def after_enter(parse_tree, symbol_table, children):
    """ variable: type ident """
    if parse_tree.data == "variable":
        variable = Variable(children[1].text, Type(children[0].text))
        symbol_table.last_scope().push_variable(variable)
        return f'''
        addi $sp, $sp, -{variable.type.size}
        ''', Type()

    """ lvalue: ident |  class_val | array_val """
    if parse_tree.data == "lvalue":  # DOTO array, class
        diff = symbol_table.get_address_diff(children[0].text)
        var = symbol_table.get_variable(children[0].code)
        symbol_table.last_scope().push_variable(Variable("__IGNORE", var.type))
        return f'''
        \taddi $t0, $sp, {diff}
        \tsw $t0, 0($sp)
        \taddi $sp, $sp, -4
        ''', Type()

    # assignment_expr_empty: lvalue "=" expr
    elif parse_tree.data == "assignment_expr_empty":
        variable_code = children[0].code
        expr_code = children[1].code
        symbol_table.last_scope().pop_variable()
        symbol_table.last_scope().pop_variable()
        return f'''{variable_code} {expr_code}
            \tlw $t0, {children[1].type.size}($sp)
            \tlw $t1, {children[1].type.size + children[0].type.size}($sp)
            \tsw $t0, 0($t1)
            \taddi $sp, $sp, {children[1].type.size + children[0].type.size}
        ''', Type()

    # assignment_expr_with_plus: lvalue "+=" expr
    elif parse_tree.data == "assignment_expr_with_plus":
        variable_code = children[0].code
        expr_code = children[1].code
        symbol_table.last_scope().pop_variable()
        symbol_table.last_scope().pop_variable()
        return f'''{variable_code} {expr_code}
            \tlw $t0, {children[1].type.size}($sp)
            \tlw $t1, {children[1].type.size + children[0].type.size}($sp)
            \tlw $t2, 0($t1)
            \tadd $t0, $t0, $t2
            \tsw $t0, 0($t1)
            \taddi $sp, $sp, {children[1].type.size + children[0].type.size}
        ''', Type()

    # assignment_expr_with_min: lvalue "-=" expr
    elif parse_tree.data == "assignment_expr_with_min":
        variable_code = children[0].code
        expr_code = children[1].code
        symbol_table.last_scope().pop_variable()
        symbol_table.last_scope().pop_variable()
        return f'''{variable_code} {expr_code}
            \tlw $t0, {children[1].type.size}($sp)
            \tlw $t1, {children[1].type.size + children[0].type.size}($sp)
            \tlw $t2, 0($t1)
            \tsub $t0, $t2, $t0
            \tsw $t0, 0($t1)
            \taddi $sp, $sp, {children[1].type.size + children[0].type.size}
        ''', Type()

    # assignment_expr_with_mul: lvalue "*=" expr
    elif parse_tree.data == "assignment_expr_with_mul":
        variable_code = children[0].code
        expr_code = children[1].code
        symbol_table.last_scope().pop_variable()
        symbol_table.last_scope().pop_variable()
        return f'''{variable_code} {expr_code}
            \tlw $t0, {children[1].type.size}($sp)
            \tlw $t1, {children[1].type.size + children[0].type.size}($sp)
            \tlw $t2, 0($t1)
            \tmul $t0, $t2, $t0
            \tsw $t0, 0($t1)
            \taddi $sp, $sp, {children[1].type.size + children[0].type.size}
        ''', Type()

    # assignment_expr_with_div: lvalue "/=" expr
    elif parse_tree.data == "assignment_expr_with_div":
        variable_code = children[0].code
        expr_code = children[1].code
        symbol_table.last_scope().pop_variable()
        symbol_table.last_scope().pop_variable()
        return f'''{variable_code} {expr_code}
            \tlw $t0, {children[1].type.size}($sp)
            \tlw $t1, {children[1].type.size + children[0].type.size}($sp)
            \tlw $t2, 0($t1)
            \tdiv $t0, $t2, $t0
            \tsw $t0, 0($t1)
            \taddi $sp, $sp, {children[1].type.size + children[0].type.size}
        ''', Type()

    # constant: doubleconstant | constant_token | boolconstant
    elif parse_tree.data == "constant":  # TODO only int
        symbol_table.last_scope().push_variable(Variable("__IGNORE", children[0].type))
        return f''' \tsub $t0, $t0, $t0
                    \taddi $t0, $t0, {children[0].text}
                    \tsw $t0, 0($sp)
                    \taddi $sp, $sp, -{children[0].type.size}
                ''', Type()

    # math_expr_sum: expr "+" expr
    elif parse_tree.data == "math_expr_sum":
        left_expr_code = children[0].code
        right_expr_code = children[1].code
        symbol_table.last_scope().pop_variable()
        return f'''{left_expr_code} {right_expr_code}
                    \tlw $t0, {children[1].type.size}($sp)
                    \tlw $t1, {children[1].type.size + children[0].type.size}($sp)
                    \tadd $t0, $t0, $t1
                    \taddi $sp, $sp, {children[1].type.size + children[0].type.size}
                    \tsw $t0, 0($sp)
                    \taddi $sp, $sp, -4
                ''', Type()
    elif parse_tree.data == "ifstmt":
        label = children[1].scope.end_labele
        symbol_table.last_scope().pop_variable()
        expr_code = children[0].code
        stmt_if_code = children[1].code
        if len(children) == 2:
            return f'''{expr_code}
                \tlw $t0, {children[1].type.size}($sp)
                \taddi $sp, $sp, 4
                \tsub $t1, $t1, $t1
                \tbeq $t0, $t1, {label}
                {stmt_if_code}
                {label}:            
            ''', Type()
        else:
            stmt_else_code = children[2].code
            label_end = children[2].scope.end_labele
            return f'''{expr_code}
                            \tlw $t0, {children[1].type.size}($sp)
                            \taddi $sp, $sp, 4
                            \tsub $t1, $t1, $t1
                            \tbeq $t0, $t1, {label}
                            {stmt_if_code}
                            \tj {label_end}
                            {label}:
                            {stmt_else_code}  
                            {label_end}:          
                        ''', Type()


    elif parse_tree.data == "condition_expr_less":
        left_expr_code = children[0].code
        right_expr_code = children[1].code
        symbol_table.last_scope().pop_variable()  # t0 right t1 left
        return f'''{left_expr_code} {right_expr_code} 
                    \tlw $t0, {children[1].type.size}($sp)
                    \tlw $t1, {children[1].type.size + children[0].type.size}($sp)
                    \tslt $t0, $t1, $t0
                    \taddi $sp, $sp, {children[1].type.size + children[0].type.size}
                    \tsw $t0, 0($sp)
                    \taddi $sp, $sp, -4
                ''', Type()
    # math_expr_minus: expr "-" expr
    elif parse_tree.data == "printstmt":
        code = "".join(children_return)
        sum = 0
        for t in children_type:
            sum += t.size

        for child_type in reversed(children_type):
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
            sum -= child_type.size
        code += f'''
            \taddi $sp, $sp, {sum}
            \tli $a0, 10
            \tli $v0, 11  
            \tsyscall
        '''
        return code, Type()


    elif parse_tree.data == "math_expr_minus":
        left_expr_code = children_return[0]
        right_expr_code = children_return[1]
        symbol_table.last_scope().pop_variable()
        return f'''{left_expr_code} {right_expr_code}
                    \tlw $t0, {children_type[1].size}($sp)
                    \tlw $t1, {children_type[1].size + children_type[0].size}($sp)
                    \tsub $t0, $t1, $t0
                    \taddi $sp, $sp, {children_type[1].size + children_type[0].size}
                    \tsw $t0, 0($sp)
                    \taddi $sp, $sp, -4
                ''', Type()

    # math_expr_minus: expr "*" expr
    elif parse_tree.data == "math_expr_mul":
        left_expr_code = children_return[0]
        right_expr_code = children_return[1]
        symbol_table.last_scope().pop_variable()
        return f'''{left_expr_code} {right_expr_code}
                    \tlw $t0, {children_type[1].size}($sp)
                    \tlw $t1, {children_type[1].size + children_type[0].size}($sp)
                    \tmul $t0, $t1, $t0
                    \taddi $sp, $sp, {children_type[1].size + children_type[0].size}
                    \tsw $t0, 0($sp)
                    \taddi $sp, $sp, -4
                ''', Type()

    # math_expr_div: expr "/" expr
    elif parse_tree.data == "math_expr_div":
        left_expr_code = children_return[0]
        right_expr_code = children_return[1]
        symbol_table.last_scope().pop_variable()
        return f'''{left_expr_code} {right_expr_code}
                    \tlw $t0, {children_type[1].size}($sp)
                    \tlw $t1, {children_type[1].size + children_type[0].size}($sp)
                    \tdiv $t0, $t1, $t0
                    \taddi $sp, $sp, {children_type[1].size + children_type[0].size}
                    \tsw $t0, 0($sp)
                    \taddi $sp, $sp, -4
                ''', Type()


    # lvalue_exp: lvalue
    elif parse_tree.data == "lvalue_exp":
        return f'''{children_return[0]}
                            \tlw $t0, 4($sp)
                            \tlw $t1, 0($t0)
                            \tsw $t1, 4($sp)
                        ''', Type()

    elif parse_tree.data == "stmtblock":
        symbol_table.pop_scope()
        code = f'''
        \t{symbol_table.last_scope().begin_lable}
        '''
        code = "".join(children_return)
        code += f'''
        \t{symbol_table.last_scope().end_labele}
        '''
        return "".join(children_return), Type()
    else:
        return "".join(children_return), Type()
