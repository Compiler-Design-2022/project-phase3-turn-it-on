import re
from lark import Lark

grammer = r"""
    program: macro* decl+
    macro: "import" ESCAPED_STRING
    decl: variable_decl | function_decl | class_decl | interface_decl
    variable_decl: variable ";"
    variable: type ident
    type: /int/ | /double/ | /bool/ | /string/ | ident | type "[]" 
    function_decl: type ident "(" formals ")" stmtblock | /void/ ident "(" formals ")" stmtblock 
    formals: variable ("," variable)+ |  variable | null
    class_decl: "class" ident ("extends" ident)? ("implements" ident ("," ident)*)? "{" field* "}"
    field: access_mode variable_decl | access_mode function_decl
    access_mode: /private/ | /public/ | /protected/ | null
    interface_decl: "interface" ident "{" prototype* "}"
    prototype: type ident "(" formals ")"";" | /void/ ident "(" formals ")" ";" 
    stmtblock: "{" variable_decl* stmt* "}" | mipscode
    mipscode: "~"/[^~]+/"~"
    stmt: expr? ";" | ifstmt | whilestmt | whilestmt | forstmt | breakstmt | continuestmt | returnstmt | printstmt | stmtblock     
    ifstmt: "if""(" expr ")" stmt ("else" stmt)?
    whilestmt: "while""(" expr ")" stmt
    forstmt: "for" "(" first_forstmt_part ";" expr ";" third_forstmt_part ")" stmt
    first_forstmt_part: expr?
    third_forstmt_part: expr?
    returnstmt: "return" expr? ";"
    breakstmt: "break" ";"
    continuestmt: "continue" ";"
    printstmt: "Print" "(" expr ("," expr)* ")" ";"
    expr: assignment_expr | constant | lvalue_exp | this_expr | call | "(" expr ")" | math_expr_minus | math_expr_sum | math_expr_mul | math_expr_div | math_expr_mod  | sign_expr | condition_expr | bool_math_expr
          | new_expr | new_array_expr | type_change_expr | len_expr
    
    len_expr: "@len" "(" expr ")"
    lvalue_exp: lvalue
    this_expr: "this"
    new_expr: "new" ident
    new_array_expr: "NewArray" "(" expr "," type ")"
    assignment_expr: assignment_expr_empty | assignment_expr_with_plus | assignment_expr_with_mul | assignment_expr_with_div | assignment_expr_with_min
    not_expr:  "!" expr
    sign_expr: "-" expr
    condition_expr: condition_expr_less | condition_expr_less_equal | condition_expr_greater | condition_expr_greater_equal | condition_expr_equal | condition_expr_not_equal
    bool_math_expr: bool_math_expr_and | bool_math_expr_or
    type_change_expr: type_change_expr_itod | type_change_expr_dtoi | type_change_expr_itob | type_change_expr_btoi
    
    assignment_expr_empty: lvalue "=" expr
    assignment_expr_with_plus: lvalue "+=" expr
    assignment_expr_with_mul: lvalue "*=" expr
    assignment_expr_with_div: lvalue "/=" expr
    assignment_expr_with_min: lvalue "-=" expr

    math_expr_minus: expr "-" expr
    math_expr_sum: expr "+" expr
    math_expr_mul: expr "*" expr
    math_expr_div: expr "/" expr
    math_expr_mod: expr "%" expr

    condition_expr_less: expr "<" expr
    condition_expr_less_equal: expr "<=" expr
    condition_expr_greater: expr ">" expr
    condition_expr_greater_equal: expr ">=" expr
    condition_expr_equal: expr "==" expr
    condition_expr_not_equal: expr "!=" expr

    bool_math_expr_and: expr "&&" expr
    bool_math_expr_or: expr "||" expr

    type_change_expr_itod: "itod(" expr ")"
    type_change_expr_dtoi: "dtoi(" expr ")"
    type_change_expr_itob: "itob(" expr ")"
    type_change_expr_btoi: "btoi(" expr ")"


    lvalue: ident |  class_val | array_val
    class_val: expr "." ident
    array_val: expr "[" expr "]" 
    
    call:  normal_function_call | class_function_call
    class_function_call: expr "." ident "(" actuals ")" 
    normal_function_call: ident "(" actuals ")"
    
    actuals: expr ("," expr)* | null
    constant: doubleconstant | constant_token | boolconstant  
    constant_token: INT | STRING | base16 | "null"
    null:
    ident: /@[a-zA-Z][a-zA-Z0-9_]*/ | /@__func__[a-zA-Z0-9_]*/ | /@__line__[a-zA-Z0-9_]*/ 
    doubleconstant: /[0-9]+/"."/[0-9]+/ | /[0-9]+/"." | /[0-9]+/"."/[0-9]*[Ee][+-]?[0-9]+/
    boolconstant: boolconstant_true | boolconstant_false
    boolconstant_true: "true"
    boolconstant_false: "false"
    base16: /0[xX][0-9a-fA-F]+/
    INT: /[0-9]+/
    STRING : /"[^"]*"/
    
    %import common.ESCAPED_STRING
    %import common.WS
    %ignore WS
"""
json_parser = Lark(grammer, start='program', parser='lalr')


def remove_comment(s):
    s = s.replace("//", "@")
    s = re.sub("@[^\n]*", "", s)
    s = s.replace("/*", "#")
    s = s.replace("*/", "@")
    s = re.sub("#[^#@]*@", "", s)
    return s


def reprep(string):
    keywords = "define, true, false, return, void, int, double, bool, string, class, interface, null, this, extends, implements, for, while, if, else, return, break, continue, new, NewArray, Print, dtoi, itod, btoi, itob, private, protected, public, import".split(
        ", ")
    if string not in keywords and (
            re.match("[a-zA-Z][a-zA-Z0-9_]*", string) or re.match("__func__[a-zA-Z0-9_]*", string) or re.match(
        "__line__[a-zA-Z0-9_]*", string)):
        return "@" + string
    else:
        return string


def replace_ident(string):
    stopWords = ['.', ' ', '\n', ']', '[', '(', ')', ';', '!', '-', '\t', '*', '+', '=', '<', '>', '/', '%', ',']
    ans = ""
    current = ""
    for i in range(len(string)):
        if string[i] in stopWords:
            ans += reprep(current)
            current = ""
            ans += string[i]
        else:
            current += string[i]
    ans += reprep(current)

    return ans


def linker_add_imports(string):
    ans = ""
    list = string.split("\n")
    for line in list:
        sp_line = line.split()
        if len(sp_line) == 2 and sp_line[0] == "import" and len(sp_line[1]) > 2 and sp_line[1][0] == '"' and sp_line[1][
            len(sp_line[1]) - 1] == '"':
            parser(open(sp_line[1][1:-1]).read())
    return ans


def parser(string):
    if string.find("print") != -1:
        print("RIDI")
        raise ValueError
    string = replace_defines(string + ' ')
    string = remove_comment(string)
    string = string.replace(");", ") ;")
    # linker_add_imports(string)
    string = replace_ident(string)
    string = re.sub("\[[ ]+\]", '[]', string)
    print(string)
    for x in string: 
        print(x, end="---") 
    return json_parser.parse(string), string


def replace_line(define_map, line):
    """replace line with defined map of previous line"""
    line = re.split('( |"|\[|]|\(|\)|;|\n|\t)', line)
    for i in range(len(line)):
        if line[i] in define_map:
            line[i] = define_map[line[i]]
    answer = ""
    for i in line:
        answer += i
    return answer


def replace_defines(input):
    """replace lines with defined map with iteration"""
    input_lines = input.split("\n")
    define_map = {}
    answer = ""
    pref = True
    for line in input_lines:
        line = replace_line(define_map, line)
        split_form = line.split()
        if len(split_form) >= 1 and split_form[0] != "define" and split_form[0] != "import":
            pref = False
        if len(split_form) >= 3 and split_form[0] == 'define' and pref:
            # add key value of define to map
            define_map[split_form[1]] = " ".join(split_form[2:])
        else:
            answer += line + "\n"

    return answer

# print(parser(open(f"../tests/in-out/t205-define.in").read()).pretty())
