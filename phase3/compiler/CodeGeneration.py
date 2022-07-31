from SymbolTable import SymbolTable, Scope, Variable, Type
import lark


def cgen_token(token: lark.Token, symboltable: SymbolTable):
    return token.value, Type()


def cgen(parse_tree, symbol_table: SymbolTable):
    if parse_tree.__class__ is lark.Token:
        return cgen_token(parse_tree, symbol_table)

    print("^" * 60, parse_tree.data, parse_tree._meta)
    before_enter(parse_tree, symbol_table)
    children_return = []
    children_type = []
    for child in parse_tree.children:
        child_code, child_type = cgen(child, symbol_table)
        children_type.append(child_type)
        children_return.append(child_code)
        middle_enter(children_return, children_type, parse_tree, symbol_table)

    mips_code, result_type = after_enter(parse_tree, symbol_table, children_return, children_type)
    return mips_code, result_type


def before_enter(parse_tree, symbol_table):
    if parse_tree.data == "stmtblock":
        symbol_table.push_scope(Scope())
    return


def middle_enter(children_code, children_type, parse_tree, symbol_table):
    pass


def after_enter(parse_tree, symbol_table, children_return, children_type):
    """ variable: type ident """
    if parse_tree.data == "variable":
        variable = Variable(children_return[1], Type(children_return[0]))
        symbol_table.last_scope().push_variable(variable)
        return f'''
        addi $sp, $sp, -{variable.type.size}
        ''', Type()

    """ lvalue: ident |  class_val | array_val """
    if parse_tree.data == "lvalue":  # DOTO array, class
        diff = symbol_table.get_address_diff(children_return[0])
        var = symbol_table.get_variable(children_return[0])
        symbol_table.last_scope().push_variable(Variable("__IGNORE", var.type))
        return f'''
        \taddi $t0, $sp, {diff}
        \tsw $t0, 0($sp)
        \taddi $sp, $sp, -4
        ''', Type()
    
    # assignment_expr_empty: lvalue "=" expr
    elif parse_tree.data == "assignment_expr_empty":
        variable_code = children_return[0]
        expr_code = children_return[1]
        symbol_table.last_scope().pop_variable()
        symbol_table.last_scope().pop_variable()
        return f'''{variable_code} {expr_code}
            \tlw $t0, {children_type[1].size}($sp)
            \tlw $t1, {children_type[1].size + children_type[0].size}($sp)
            \tsw $t0, 0($t1)
            \taddi $sp, $sp, {children_type[1].size + children_type[0].size}
        ''', Type()
    
    # assignment_expr_with_plus: lvalue "+=" expr
    elif parse_tree.data == "assignment_expr_with_plus":
        variable_code = children_return[0]
        expr_code = children_return[1]
        symbol_table.last_scope().pop_variable()
        symbol_table.last_scope().pop_variable()
        return f'''{variable_code} {expr_code}
            \tlw $t0, {children_type[1].size}($sp)
            \tlw $t1, {children_type[1].size + children_type[0].size}($sp)
            \tlw $t2, 0($t1)
            \tadd $t0, $t0, $t2
            \tsw $t0, 0($t1)
            \taddi $sp, $sp, {children_type[1].size + children_type[0].size}
        ''', Type()
    
    # assignment_expr_with_min: lvalue "-=" expr
    elif parse_tree.data == "assignment_expr_with_min":
        variable_code = children_return[0]
        expr_code = children_return[1]
        symbol_table.last_scope().pop_variable()
        symbol_table.last_scope().pop_variable()
        return f'''{variable_code} {expr_code}
            \tlw $t0, {children_type[1].size}($sp)
            \tlw $t1, {children_type[1].size + children_type[0].size}($sp)
            \tlw $t2, 0($t1)
            \tsub $t0, $t2, $t0
            \tsw $t0, 0($t1)
            \taddi $sp, $sp, {children_type[1].size + children_type[0].size}
        ''', Type()
    
    # assignment_expr_with_mul: lvalue "*=" expr
    elif parse_tree.data == "assignment_expr_with_mul":
        variable_code = children_return[0]
        expr_code = children_return[1]
        symbol_table.last_scope().pop_variable()
        symbol_table.last_scope().pop_variable()
        return f'''{variable_code} {expr_code}
            \tlw $t0, {children_type[1].size}($sp)
            \tlw $t1, {children_type[1].size + children_type[0].size}($sp)
            \tlw $t2, 0($t1)
            \tmul $t0, $t2, $t0
            \tsw $t0, 0($t1)
            \taddi $sp, $sp, {children_type[1].size + children_type[0].size}
        ''', Type()

    # assignment_expr_with_div: lvalue "/=" expr
    elif parse_tree.data == "assignment_expr_with_div":
        variable_code = children_return[0]
        expr_code = children_return[1]
        symbol_table.last_scope().pop_variable()
        symbol_table.last_scope().pop_variable()
        return f'''{variable_code} {expr_code}
            \tlw $t0, {children_type[1].size}($sp)
            \tlw $t1, {children_type[1].size + children_type[0].size}($sp)
            \tlw $t2, 0($t1)
            \tdiv $t0, $t2, $t0
            \tsw $t0, 0($t1)
            \taddi $sp, $sp, {children_type[1].size + children_type[0].size}
        ''', Type()

    # constant: doubleconstant | constant_token | boolconstant  
    elif parse_tree.data == "constant":  # TODO only int
        symbol_table.last_scope().push_variable(Variable("__IGNORE", children_type[0]))
        return f''' \tsub $t0, $t0, $t0
                    \taddi $t0, $t0, {children_return[0]}
                    \tsw $t0, 0($sp)
                    \taddi $sp, $sp, -{children_type[0].size}
                ''', Type()

    # math_expr_sum: expr "+" expr
    elif parse_tree.data == "math_expr_sum":
        left_expr_code = children_return[0]
        right_expr_code = children_return[1]
        symbol_table.last_scope().pop_variable()
        return f'''{left_expr_code} {right_expr_code}
                    \tlw $t0, {children_type[1].size}($sp)
                    \tlw $t1, {children_type[1].size + children_type[0].size}($sp)
                    \tadd $t0, $t0, $t1
                    \taddi $sp, $sp, {children_type[1].size + children_type[0].size}
                    \tsw $t0, 0($sp)
                    \taddi $sp, $sp, -4
                ''', Type()
    
    # math_expr_minus: expr "-" expr
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
        return "".join(children_return), Type()
    else:
        return "".join(children_return), Type()
