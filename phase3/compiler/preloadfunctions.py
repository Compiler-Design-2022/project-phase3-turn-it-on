
type_change_function_inside4to4 = '''
    ~mips
    lw $t0, 12($sp) 
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
    if(a==0){
        return false;
    }else{
        return true;
    }
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
    ~mips
    lw $t0, 12($sp) 
    lb $t1, 4($sp)
    sw $t1, 0($sp) 
    addi $sp, $sp, -4
    jr $t0
    ~
}
int dtoi(double a){
    ~mips
    lw $t0, 12($sp) 
    lw $t1, 4($sp)
     mtc1 $t1, $f12
    cvt.s.w $f12, $f12
    sw $t0, 0($sp) 
    addi $sp, $sp, -4
    jr $t0
    ~
}
int getsp(){
    ~mips
    lw $t0, 8($sp) 
    sw $sp, 0($sp) 
    addi $sp, $sp, -4
    jr $t0
    ~
}
int getGSA(){
    ~mips
    lw $t0, 8($sp) 
    lw $t1, 4($sp)
    sw $t1, 0($sp) 
    addi $sp, $sp, -4
    jr $t0
    ~
}
double itod(int a){
    ''' + type_change_function_inside4to4 + '''
}''' + '''
int ReadChar(){
    ~mips
    li $v0, 12           #read_char 
    syscall             #ReadChar 
    lw $t0, 8($sp) 
    sw $v0, 0($sp) 
    addi $sp, $sp, -4
    jr $t0
    ~
}


char[] ReadLine(){
        char[] res; 
        int inp; 
        int size;
        int bufsize;
        size=0;
        bufsize=100;
        res=NewArray(100, char);                                                                                                   
        while(true){ 
            inp = ReadChar(); 
            if (inp == 10){ 
                break; 
            }
            if(size==bufsize){
                res=res+NewArray(100, char);
                bufsize+=100;
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
                    if (inp <58 && 48<=inp){
                        res = (res * 10) + (inp - 48);
                    } 
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
    }
    for(i=0;i<bl;i+=1){
        ans[al+i]=b[i];
    }
    return catos(ans);
}
bool string_equality_check(string a, string b){
    int al;
    int bl;
    int i;
    al=ctoi(a[-1]);
    bl=ctoi(b[-1]);
    if (al!=bl){
        return false;
    }
    for(i=0;i<bl;i+=1){
        int x;
        int y;
        x=ctoi(a[i]);
        y=ctoi(b[i]);
        if(x!=y){
            return false;
        }
    }
    return true;
}
'''