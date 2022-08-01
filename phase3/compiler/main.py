from os import listdir
from parserC import parser
from CodeGeneration import cgen
from SymbolTable import SymbolTable, Scope


def run(input_file_address: str) -> bool:
    # input_file = open(input_file_address)
    # input_content = input_file.read()
    input_content = """
    int main() {
        int a;
        int i;
        a=3;
        i = 0;
        for(i=0;i<2;i+=1)
        {
            if (3<a)
            {
                continue; 
            }
            a = a + 1;
            i = i + 1; 
        }

        Print(a);
    }"""
    try:
        print(input_content)
        parse_tree, code = parser(input_content)
        print(parse_tree.pretty())
        # print(parse_tree)
        try:
            symbol_table = SymbolTable()
            symbol_table.push_scope(Scope())
            mips_code = cgen(parse_tree, symbol_table).code
            print(mips_code)
            return mips_code
        except Exception:
            print("Semantic Error")
            raise ValueError
    except:
        print("Syntax Error")
        raise ValueError

    return None


run(None)
# all_tests = {}
# for f in listdir('./'):
#     all_tests[f.split('.')[0]] = True
#
# name = "test"
# # open(f"tests/in-out/{name}.out").read().rstrip().lstrip()
# res = run(f"tests/in-out/{name}.in")

# correct = 0
# error = 0
# total = 0
# wrongs = []
# for step, name in enumerate(all_tests.keys()):
#     total += 1
#     try:
#         answer = open(f"../tests/in-out/{name}.out").read().rstrip().lstrip()
#         res = run(f"../tests/in-out/{name}.in")
#         if res and answer == "OK":
#             # print("OK", step)
#             correct += 1
#         elif not res and answer != "OK":
#             # print("OK", step)
#             correct += 1
#         else:
#             wrongs.append(step)
#             print(res,answer, answer.rstrip().lstrip()=="OK",name)
#             print("WRONG ", step)
#     except:
#         error += 1
#         print("ERROR on", name)
# #
# # print("total=", total, "Correct=", correct, "Wrong=", total - error - correct, "Error=", error)
# # print(wrongs)
# # step = int(input("which test to investigate?"))
# # name = list(all_tests.keys())[step]
# # answer = open(f"../tests/in-out/{name}.out").read()
# # text = open(f"../tests/in-out/{name}.in").read()
# # print(text)
# # print("name=", name)
# # print("answer=", answer)
# # print(parser(text).pretty())