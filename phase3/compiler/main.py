from os import listdir
from parserC import parser
from CodeGeneration import cgen, function_declaration
from SymbolTable import SymbolTable, Scope


def run(input_file_address: str) -> bool:
    # input_file = open(input_file_address)
    # input_content = input_file.read()
    input_content = '''  

void sort(int[] items) {
    
    /* implementation of bubble sort */
    int i;
    int j;

    int n;
    Print(items[0], items[1], items[2], items[3]);
    n = 4;
    for (i = 0; i < n-1; i = i + 1){
        for (j = 0; j < (n - i) - 1; j = j + 1){
            if (items[j] > items[j + 1]) {
                int t;
                t = items[j];
                items[j] = items[j + 1];
                items[j + 1] = t;
            }
        }
    }


}

int main() {
    int i;
    int j;
    int[] rawitems;
    int[] items;

    Print("Please enter the numbers (max count: 100, enter -1 to end sooner): ");

    rawitems = NewArray(4, int);
    for (i = 0; i < 4; i = i + 1) {
        int x;
        x = 100-i;
        if (x == -1) break;

        rawitems[i] = x;
    }
    items = NewArray(i, int);

    // copy to a more convenient location
    for (j = 0; j < i; j = j + 1) {
        items[j] = rawitems[j];
    }

    sort(items);


    Print("After sort: ");

    for (i = 0; i < 4 ; i = i + 1) {
        Print(items[i]);
    }
}


    '''

    try:
        print(input_content)
        parse_tree, code = parser(input_content)
        print(parse_tree.pretty())
        # print(parse_tree)
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
