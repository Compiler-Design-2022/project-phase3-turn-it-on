from os import listdir
from parserC import parser
from CodeGeneration import cgen, function_declaration
from SymbolTable import SymbolTable, Scope, Method, Type
from preloadfunctions import code_predified_functions

def run() -> str:
    input_content = ''' 
int main() {
    double d1;
    double d2;
    double d3;
    double d4;
    double d5;
    double d6;
    double d7;
    double d8;

    bool r;

    d1 = 69.82413714;
    d2 = 960.7071281;
    d3 = 0.5281794697;
    d4 = 0.5281794697;
    d5 = -5039.128903;
    d6 = 7585.800593;
    d7 = -11748.63533;
    d8 = -13446.89678;

    r = d1 < d2;
    Print(r);

    r = d3 < d4;
    Print(r);

    r = d5 < d6;
    Print(r);

    r = d7 < d8;
    Print(r);

}


    '''

    try:
        print(input_content)
        parse_tree, code = parser(input_content)
        print(parse_tree.pretty())
        try:
            symbol_table = SymbolTable()
            symbol_table.push_scope(Scope())
            function_declaration(parse_tree, symbol_table)
            mips_code = cgen(parse_tree, symbol_table).code
            with open("OUTPUT.txt", mode="w") as f:
                f.write(mips_code)
            print(mips_code)
            return mips_code
        except Exception:
            print("Semantic Error")
            raise ValueError
    except:
        print("Syntax Error")
        raise ValueError


run()
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

# """
# int main(){
#     int i;
#     int j;
#     int k;
#     int[][][] a;
#     int y;
#     y=9;
#     a = NewArray(3, int[][]);
#     for(i = 0; i < 3; i = i+1){
#         a[i] = NewArray(i+1, int[]);
#     }
#     for(i = 0; i < 3; i = i+1){
#         for(j = 0; j <= i; j = j+1){
#             a[i][j] = NewArray(3, int);
#             for(k = 0; k < 3; k = k+1){
#                 a[i][j][k] = k;
#             }
#         }
#     }
#
#     for(i = 0; i < 3; i = i+1){
#         for(j = 0; j <= i; j = j+1){
#             for(k = 0; k < 3; k = k+1){
#                 Print(i, j, j, j, k, a[i][j][k]);
#                 if(k<2){
#                     int u;
#                     continue;
#                 }else{
#                     break;
#                 }
#             }
#         }
#     }
#     Print(y);
#
# }
#     """
