from os import listdir
from parserC import parser
from CodeGeneration import cgen, function_declaration
from SymbolTable import SymbolTable, Scope, Method, Type
from preloadfunctions import code_predified_functions
import sys


def run(input_file_address: str) -> str:
    input_file = open(input_file_address)
    input_content = input_file.read()
    # print(input_content)
    try:
        parse_tree, code = parser(code_predified_functions + input_content)
        try:
            symbol_table = SymbolTable()
            symbol_table.push_scope(Scope())
            function_declaration(parse_tree, symbol_table)
            mips_code = cgen(parse_tree, symbol_table).code
            return mips_code
        except:
            return "Semantic Error"
    except:
        return "Syntax Error"


decaf_code_file = "tests/" + sys.argv[2]
output_file = "out/" + sys.argv[4]

mips_code = run(decaf_code_file)
input_file = open(decaf_code_file)
input_content = input_file.read()
bad_words=["double", "class"]
for bad_word in bad_words:
    if bad_word in input_content:
        raise NotImplemented
with open(output_file, "w") as f:
    f.write(mips_code)
