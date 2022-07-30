from os import listdir
from parserC import parser
from phase3.compiler.CodeGeneration import cgen
from phase3.compiler.SymbolTable import SymbolTable


def run(input_file_address: str) -> bool:
    input_file = open(input_file_address)
    input_content = input_file.read()
    input_content = """
    int main() {
        int a;
        a=(b*5);
    }"""
    try:
        parse_tree, code = parser(input_content)
        print(parse_tree.pretty())
        # print(parse_tree)
        try:
            return cgen(parse_tree, SymbolTable())
        except Exception:
            print("Semantic Error")
            raise ValueError
    except:
        print("Syntax Error")
        raise ValueError

    return None


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
