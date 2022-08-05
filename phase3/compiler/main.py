from os import listdir
from parserC import parser
from CodeGeneration import cgen, function_declaration
from SymbolTable import SymbolTable, Scope, Method, Type

type_change_function_inside4to4 = '''
    ~mips
    lw $t0, 8($sp) 
    lw $t1, 4($sp)
    sw $t1, 0($sp) 
    addi $sp, $sp, -4
    jr $t0
    ~
'''
code_predified_functions = '''
char itoc(int a){
    ''' + type_change_function_inside4to4 + '''
}
bool itob(int a){
    ''' + type_change_function_inside4to4 + '''
}
int btoi(bool a){
    ''' + type_change_function_inside4to4 + '''
}
int ctoi(char a){
    ''' + type_change_function_inside4to4 + '''
}
int dtoi(double a){
    ''' + type_change_function_inside4to4 + '''
}
double itod(int a){
    ''' + type_change_function_inside4to4 + '''
}''' + '''
int ReadChar(){
    ~mips
    li $v0, 12           #read_char 
    syscall             #ReadChar 
    lw $t0, 4($sp) 
    sw $v0, 0($sp) 
    addi $sp, $sp, -4
    jr $t0
    ~
}


char[] ReadLine(){
        char[] res; 
        int inp; 
        int size;
        
        size=0;
        res=NewArray(100, char);                                                                                                   
        while(true){ 
            inp = ReadChar(); 
            if (inp == 10){ 
                break; 
            }
            res[size] = itoc(inp); 
            size+=1;
        } 
        res[-1]=itoc(size);
        return res; 
}
int ReadInteger(){
        int res; 
        int inp; 
        int sign; 
        sign = 1; 
        res = 0; 
        while(true){ 
            inp = ReadChar(); 
            if (inp == 10){ 
                break; 
            }
            if (inp != 43){ 
                if (inp == 45){ 
                    sign = -1; 
                }else{  
                    res = (res * 10) + (inp - 48); 
                } 
            } 
        } 
        return res * sign; 
}
'''


def run(input_file_address: str) -> bool:
    # input_file = open(input_file_address)
    # input_content = input_file.read()
    input_content = ''' 
        int main() {
            Print(ReadLine());
        }
    '''

    try:
        print(input_content)
        parse_tree, code = parser(code_predified_functions + input_content)
        print(parse_tree.pretty())
        # print(parse_tree)
        try:
            symbol_table = SymbolTable()
            symbol_table.push_scope(Scope())
            function_declaration(parse_tree, symbol_table)
            symbol_table.push_method(Method("ReadChar", Type("char"), []))
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
