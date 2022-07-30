from SymbolTable import SymbolTable, Scope, Variable, Type
import lark


def cgen_token(token: lark.Token, symboltable: SymbolTable):
    return token.value, Type()


def cgen(parse_tree, symbol_table: SymbolTable):
    if parse_tree.__class__ is lark.Token:
        return cgen_token(parse_tree, symbol_table)

    print("^" * 60, parse_tree.data, parse_tree._meta)

    before_enter(parse_tree, symbol_table)
    child_return = []
    for child in parse_tree.children:
        child_code, child_type=cgen(child, symbol_table)
        child_return.append(child_code)

    mips_code, result_type = after_enter(parse_tree, symbol_table, child_return)
    return mips_code, result_type


def before_enter(parse_tree, symbol_table):
    if parse_tree.data == "stmtblock":
        symbol_table.push_scope(Scope())

    return


def after_enter(parse_tree, symbol_table, child_return):
    if parse_tree.data == "variable":
        variable = Variable(child_return[1], Type(child_return[0]))
        symbol_table.last_scope().push_variable(variable)
        return f'''
        addi $sp, $sp, -{variable.type.size}\n
        ''', None
    elif parse_tree.data == "assignment_expr_empty":
        variable_name = child_return[0]
        expr_code = child_return[1]
        return f'''{expr_code}
            \tlw $t0, 4($sp)\n
            \taddi $sp, $sp, 4\n
            \tsw $t0, {symbol_table.get_address_diff(variable_name)}($sp)\n
        ''', Type()

    elif parse_tree.data == "constant":
        value = child_return[0]
        return f'''
            \taddi $sp, $sp, -4\n
            \tli $t0, {value}\n
            \tsw $t0, 4($sp)\n
        ''', Type()

    elif parse_tree.data == "lvalue":
        return child_return[0], Type()

    elif parse_tree.data == "stmtblock":
        symbol_table.pop_scope()
        return "".join(child_return), Type()
    else:
        return "".join(child_return), Type()
