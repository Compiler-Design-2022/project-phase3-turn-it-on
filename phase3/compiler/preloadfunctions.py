
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
char[] stoca(string a){
    ''' + type_change_function_inside4to4 + '''
}
string catos(char[] a){
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

string math_expr_sum_4(string a, string b){
    int al;
    int bl;
    int i;
    string ans;
    al=ctoi(a[-1]);
    bl=ctoi(b[-1]);
    ans=NewArray(al+bl, char);
    for(i=0;i<al;i+=1){
        ans[i]=a[i];
        Print(i);
        Print(ans[i]);
    }
    for(i=0;i<bl;i+=1){
        ans[al+i]=b[i];
        Print(i+al);
        Print(ans[al+i]);
    }
    return catos(ans);
}
'''