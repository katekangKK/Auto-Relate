import pandas as pd
import numpy as np
import math
import itertools
import formulas

def allnum(elements):
    token = 1
    new_elements = []
    for elem in elements:
        # To prevent overflow of int64 variables, numbers greater than the square root of the maximum value of int64 have been excluded.
        if np.issubdtype(type(elem),np.integer) == True:
            new_elements.append(elem)
        # float with 'nan', 'nan' will be transformed to 0
        elif np.issubdtype(type(elem),float) == True:
            if elem != elem:
                new_elements.append(0)
            else:
                new_elements.append(elem)
        else:
            token = 0
            new_elements = elements
            break
    return(token,new_elements)

# formula = '(a+b)+(c+d)' [+,]
# class OP_Tree():

# def constant_relation_discover(data,columns,allow_rate,rel_ce,abs_ce):
#     ops = ['+', '-', '*', '/']
#     for op in ops:
#         potential_constant = {}
#         for n in range(len(data)):
#             elements = [data[columns[i]][n] for i in range(columns)]
#             token,elements = allnum(elements)
#             if token == 0:
#                 continue
            
# def op_discover(data,col_pair,col_number,allow_rate,ce):
def op_discover(data,col_list,allow_rate,rel_ce,abs_ce,skip_rows=[]): 
    # col_list = ['A','B','C','D','E']
    ardict = {}
    violation_rows = {}
    col_number = len(col_list)
    col_positions = set([i for i in range(col_number)])
    if col_number == 2:
        # print(2)
        ardict = {-1:0,0:0,1:0}
        violation_rows = {-1:[],0:[],1:[]}
        for n in range(len(data)):
            if n in skip_rows:
                continue
            elements = [data[col_list[i]][n] for i in range(col_number)]
            token,elements = allnum(elements)
            if token == 0:
                continue
            lhs,rhs = elements[0],elements[1]
            if math.isclose(lhs,rhs,rel_tol=rel_ce,abs_tol=abs_ce):
                ardict[1] += 1
                violation_rows[0].append(n)
                if rhs == 0:
                    ardict[-1] += 1
                else:
                    violation_rows[-1].append(n)
            elif math.isclose(lhs,-rhs,rel_tol=rel_ce,abs_tol=abs_ce):
                ardict[-1] += 1
                violation_rows[1].append(n)
                violation_rows[0].append(n)
            else:
                ardict[0] += 1
                violation_rows[1].append(n)
                violation_rows[-1].append(n)
                
            if (n-len(skip_rows)-max(ardict[1],ardict[-1])) > (len(data)-len(skip_rows))*allow_rate:
                return('negative',ardict,[])
        
    elif col_number == 3:
        # print(3)
        for n in range(len(data)):
            if n in skip_rows:
                continue
            # # Check whether need to stop in advance
            # # 'row_number' is defined as 'how many rows have been scanned'.
            col_val = [data[col_list[i]][n] for i in range(col_number)]
            token,col_val = allnum(col_val)
            if token == 0:
                continue
            for lhs in itertools.permutations(col_positions,col_number-1):
            # ',' is an unpacking operation, it is equivalent to 'rhs = list(col_positions - set(lhs))[0]'.
            # lhs is a list, rhs is a value.
                rhs, = list(col_positions - set(lhs))
                ops = ['+', '-', '*', '/']
                for op1, in itertools.product(ops):
                    try:
                        result = eval(f"{col_val[lhs[0]]}{op1}{col_val[lhs[1]]}")
                        if math.isclose(result,col_val[rhs],rel_tol=rel_ce,abs_tol=abs_ce):
                            if (lhs,rhs,op1) not in ardict.keys():
                                ardict[(lhs,rhs,op1)] = 1
                            else:
                                ardict[(lhs,rhs,op1)] += 1
                        else:
                            if (lhs,rhs,op1) in violation_rows.keys():
                                violation_rows[(lhs,rhs,op1)].append(n)
                            else:
                                violation_rows[(lhs,rhs,op1)] = []
                                violation_rows[(lhs,rhs,op1)].append(n)
                    except:
                        pass
            # Check whether need to stop in advance
            # 'row_number' is defined as 'how many rows have been scanned'.
            if ardict != {}:
                if (n - max(ardict.values()) - len(skip_rows)) > (len(data)-len(skip_rows))*allow_rate:
                    # print(1,n,n - max(ardict.values()))
                    return('negative',ardict,[])
            else:
                if n > (len(data)-len(skip_rows))*allow_rate:
                    # print(2,len(data)*allow_rate)
                    return('negative',ardict,[])            
        
    elif col_number == 4:
        # print(4)
        for n in range(len(data)):
            if n in skip_rows:
                continue
            col_val = [data[col_list[i]][n] for i in range(col_number)]
            token,col_val = allnum(col_val)
            if token == 0:
                continue
            for lhs in itertools.permutations(col_positions,col_number-1):
            # ',' is an unpacking operation, it is equivalent to 'rhs = list(col_positions - set(lhs))[0]'.
            # lhs is a list, rhs is a value.
                rhs, = list(col_positions - set(lhs))
                ops = ['+', '-', '*', '/']
                for op1, op2, in itertools.product(ops, ops):
                    try:
                        result = eval(f"({col_val[lhs[0]]}{op1}{col_val[lhs[1]]}){op2}{col_val[lhs[2]]}")
                        
                        if math.isclose(result,col_val[rhs],rel_tol=rel_ce,abs_tol=abs_ce):
                            if (lhs,rhs,op1,op2) not in ardict.keys():
                                ardict[(lhs,rhs,op1,op2)] = 1
                            else:
                                ardict[(lhs,rhs,op1,op2)] += 1
                        else:
                            if (lhs,rhs,op1,op2) in violation_rows.keys():
                                violation_rows[(lhs,rhs,op1,op2)].append(n)
                            else:
                                violation_rows[(lhs,rhs,op1,op2)] = []
                                violation_rows[(lhs,rhs,op1,op2)].append(n)
                    except:
                        pass
            # Check whether need to stop in advance
            # 'row_number' is defined as 'how many rows have been scanned'.
            if ardict != {}:
                if (n - max(ardict.values()) - len(skip_rows)) > (len(data)-len(skip_rows))*allow_rate:
                    # print(1,n,n - max(ardict.values()))
                    return('negative',ardict,[])
            else:
                if n > (len(data)-len(skip_rows))*allow_rate:
                    # print(2,len(data)*allow_rate)
                    return('negative',ardict,[])
                
    if ardict == {}:
        return('negative',ardict,[])    
    else:
        artype = max(ardict,key=ardict.get)
        if artype not in violation_rows.keys():
            violation_rows[artype] = []
        return(artype,ardict,violation_rows[artype])    
        
def formual_value(col_formula,batch,col_val,col_pair):
    str_lhs = col_formula[:col_formula.index('=')].strip()
    str_formula = col_formula[col_formula.index('='):]
    func = formulas.Parser().ast(str_formula)[1].compile()
    rhs = func.outputs[0]
    if col_pair == []:
        col_list_order = list(func.inputs)
        col_order_dict = {}
        for col in col_list_order:
            # col_order_dict[col] = _formula.index(col)
            # col_order_dict[col_formula.index(col)] = col
            col_order_dict[rhs.index(col)] = col
        col_list = []
        for _index in sorted(col_order_dict):
            col_list.append(col_order_dict[_index])
    else:
        col_list = col_pair[0:3]
    # first_col_lhs,first_col_rhs = rhs.split(col_list[0])[0],rhs.split(col_list[0])[1]
    # second_col_lhs,second_col_rhs = first_col_rhs.split(col_list[1])[0],first_col_rhs.split(col_list[1])[1]
    # third_col_lhs,third_col_rhs = second_col_rhs.split(col_list[2])[0],second_col_rhs.split(col_list[2])[1]
    
    first_col_lhs,first_col_rhs = rhs[:rhs.index(col_list[0])],rhs[rhs.index(col_list[0])+len(col_list[0]):]
    second_col_lhs,second_col_rhs = first_col_rhs[:first_col_rhs.index(col_list[1])],first_col_rhs[first_col_rhs.index(col_list[1])+len(col_list[1]):]
    third_col_lhs,third_col_rhs = second_col_rhs[:second_col_rhs.index(col_list[2])],second_col_rhs[second_col_rhs.index(col_list[2])+len(col_list[2]):]
    
    itmes_list = [first_col_lhs,second_col_lhs,third_col_lhs,third_col_rhs]
    
    _formula_str = itmes_list[0]+'{col_0}'+itmes_list[1]+'{col_1}'+itmes_list[2]+'{col_2}'+itmes_list[3]
    
    if batch == 0:
        result = eval(_formula_str.format(col_0 = col_val[0],col_1 = col_val[1],col_2 = col_val[2]))
    elif batch == 1:
        result = []
        for values in col_val:
            result.append(eval(_formula_str.format(col_0 = values[0],col_1 = values[1],col_2 = values[2])))
    else:
        print('batch error')
    return result

def formual_parse(col_formula,col_pair):
    str_lhs = col_formula[:col_formula.index('=')].strip()
    str_formula = col_formula[col_formula.index('='):]
    func = formulas.Parser().ast(str_formula)[1].compile()
    rhs = func.outputs[0]
    if col_pair == []:
        col_list_order = list(func.inputs)
        col_order_dict = {}
        for col in col_list_order:
            # col_order_dict[col] = _formula.index(col)
            # col_order_dict[col_formula.index(col)] = col
            col_order_dict[rhs.index(col)] = col
        col_list = []
        for _index in sorted(col_order_dict):
            col_list.append(col_order_dict[_index])
    else:
        col_list = col_pair[0:3]
    # first_col_lhs,first_col_rhs = rhs.split(col_list[0])[0],rhs.split(col_list[0])[1]
    # second_col_lhs,second_col_rhs = first_col_rhs.split(col_list[1])[0],first_col_rhs.split(col_list[1])[1]
    # third_col_lhs,third_col_rhs = second_col_rhs.split(col_list[2])[0],second_col_rhs.split(col_list[2])[1]
    
    first_col_lhs,first_col_rhs = rhs[:rhs.index(col_list[0])],rhs[rhs.index(col_list[0])+len(col_list[0]):]
    second_col_lhs,second_col_rhs = first_col_rhs[:first_col_rhs.index(col_list[1])],first_col_rhs[first_col_rhs.index(col_list[1])+len(col_list[1]):]
    third_col_lhs,third_col_rhs = second_col_rhs[:second_col_rhs.index(col_list[2])],second_col_rhs[second_col_rhs.index(col_list[2])+len(col_list[2]):]
    
    itmes_list = [first_col_lhs,second_col_lhs,third_col_lhs,third_col_rhs]
    
    _formula_str = itmes_list[0]+'{col_0}'+itmes_list[1]+'{col_1}'+itmes_list[2]+'{col_2}'+itmes_list[3]
    
    return _formula_str
    

def formual_verification(_formula_str,col_val,rel_ce,abs_ce):
    # token,col_val = allnum(col_val)
    # if token == 0:
    #     return False
        
    try:
        lhs = eval(_formula_str.format(col_0 = col_val[0],col_1 = col_val[1],col_2 = col_val[2]))
    except ZeroDivisionError:
        return False
    rhs = col_val[-1]
    if math.isclose(lhs,rhs,rel_tol=rel_ce) == False and math.isclose(lhs,rhs,abs_tol=abs_ce) == False:
        return False
    else:
        return True
    
# data1=np.random.randint(0, 100, (100, 3))
# df1 = pd.DataFrame(data1,columns=list('ABC'))

# # df1['D'] = df1['A'] + df1['B']
# df1['D'] = df1['A'] + df1['B']
# print(df1)

# artype,ardict,violation_rows = op_discover(df1,'ADB',0.20,0.1,skip_rows=[1,4])

# for cols in itertools.combinations('ABC',2):
#     print(cols)
    
# other_cols_list = []
# for col in other_cols_list:
#     col_list = col_pair + col
#     artype,ardict,violation_rows = op_discover(data,col_list,allow_rate,ce,skip_rows=[]):

