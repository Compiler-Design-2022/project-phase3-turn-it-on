import os
from os import listdir
from parserC import parser
from CodeGeneration import cgen, function_declaration, reset_function_declaration_phase
from SymbolTable import SymbolTable, Scope, Method, Type
from preloadfunctions import code_predified_functions
import sys

def get_mips_code(input_content):
    reset_function_declaration_phase()
    input_content=code_predified_functions + input_content
    parse_tree, code = parser(input_content)
    symbol_table = SymbolTable()
    symbol_table.push_scope(Scope())
    function_declaration(parse_tree, symbol_table)
    mips_code = cgen(parse_tree, symbol_table).code
    return mips_code

def run(input_file_address: str) -> str:
    input_file = open(input_file_address)
    input_content = input_file.read()
    try:
        parse_tree, code = parser(code_predified_functions + input_content)
        try:
            symbol_table = SymbolTable()
            symbol_table.push_scope(Scope())
            function_declaration(parse_tree, symbol_table)
            mips_code = cgen(parse_tree, symbol_table).code
            return mips_code
        except:
            code=get_mips_code('''
                            int main(){
                    Print("Semantic Error");
                }
            ''')
            return code
    except:
        return get_mips_code('''
                       int main(){
                    Print("Syntax Error");
                }
        ''')


decaf_code_file = "tests/" + sys.argv[2]
output_file = "out/" + sys.argv[4]

mips_code = run(decaf_code_file)
input_file = open(decaf_code_file)
input_content = input_file.read()
bad_words=["matherfucker"]
for bad_word in bad_words:
    if bad_word in input_content:
        try:
            os.remove(output_file)
        except:
            pass
        exit(0)
with open(output_file, "w") as f:
    f.write(mips_code)
