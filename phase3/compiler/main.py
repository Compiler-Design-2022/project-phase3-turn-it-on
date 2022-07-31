from os import listdir
from parserC import parser
from CodeGeneration import cgen
from SymbolTable import SymbolTable


def run(input_file_address: str) -> bool:
    # input_file = open(input_file_address)
    # input_content = input_file.read()
    input_content = """
    int main() {
        int a;
        int b;
        int c;
        a=6;
        b=3;
        b*=a;
    }"""
    try:
        print(input_content)
        input_content=input_content.replace("/", " / ")
        parse_tree, code = parser(input_content)
        print(parse_tree.pretty())
        # print(parse_tree)
        try:
            mips_code, _ = cgen(parse_tree, SymbolTable())
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
