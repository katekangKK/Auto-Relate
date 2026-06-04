import math
import itertools
import ar_tools
import numpy as np

def char_tf(elem):
    # has_tf = False
    try:
        elem = float(elem)
        if np.issubdtype(type(elem),float) == True:
            has_tf = True
        else:
            has_tf = False
    except:
        has_tf = False
        pass
    if has_tf == False:
        try:
            elem = int(elem)
            if np.issubdtype(type(elem),np.integer) == True:
                has_tf = True
            else:
                has_tf = False
        except:
            has_tf = False
            pass
    return(has_tf,elem)

def dissect(K,K_comb,artype,data,violation_rows):
    if K == 3:
        option_selection = 'single_perturb'
        lhs_index,rhs_index,op = artype
        ops = [op]
        lhs_col_one,lhs_col_two,rhs_col = K_comb[lhs_index[0]],K_comb[lhs_index[1]],K_comb[rhs_index]
        columns = [lhs_col_one,lhs_col_two,rhs_col]
        # if len(violation_rows) == 0 :
        #     violation_rows = ''
            
        lhs_cols = [lhs_col_one,lhs_col_two]
        # violation = data_processing.violation_row_to_instance(data,lhs_cols,rhs_col,violation_rows)
        formula = formula_restore(columns,[op])
        
    elif K == 4:
        option_selection = 'bound_sample_skip'
        lhs_index,rhs_index,op1,op2 = artype
        ops = [op1,op2]
        lhs_col_one,lhs_col_two,lhs_col_three,rhs_col = K_comb[lhs_index[0]],K_comb[lhs_index[1]],K_comb[lhs_index[2]],K_comb[rhs_index]
        columns = [lhs_col_one,lhs_col_two,lhs_col_three,rhs_col]
    
        lhs_cols = [lhs_col_one,lhs_col_two,lhs_col_three]
        # violation = data_processing.violation_row_to_instance(data,lhs_cols,rhs_col,violation_rows)
        formula = formula_restore(columns,[op1,op2])
        
    # return(formula,option_selection,columns,ops,violation)
    return(formula,option_selection,columns,ops)

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
        elif np.issubdtype(type(elem),str) == True:
            has_tf,elem = char_tf(elem)
            if has_tf:
                new_elements.append(elem)
            else:
                token = 0
                new_elements = elements
                break
        else:
            token = 0
            new_elements = elements
            break
    return(token,new_elements)


def isolatable(formula,columns,htcolumn_pair,matlab_eng):
    dummy_vars = ['a','b','c','d']
    for i in range(4):
        formula = formula.replace(columns[i],dummy_vars[i])
    for perturb_column_pair in htcolumn_pair.keys():
        # print(perturb_column_pair)
        # matlab_eng.isolatable_test('(a+b)*c==d',['a','b','c','d'],'a','c','+')
        # perturb_column_pair,op = ('I', 'J'),'+'
        # matlab_eng.isolatable_test(formula,columns,perturb_column_pair[0],perturb_column_pair[1],op)
        dummy_perturb_column_pair = tuple([dummy_vars[columns.index(perturb_column_pair[i])] for i in range(2)])
        for op in ['+','-','*','/']:
            # isolatable_score = matlab_eng.isolatable_test(formula,columns,perturb_column_pair[0],perturb_column_pair[1],op)
            isolatable_score = matlab_eng.isolatable_test(formula,dummy_vars,dummy_perturb_column_pair[0],dummy_perturb_column_pair[1],op)
            # print('op',isolatable_score)
            if isolatable_score == 1.0:
                htcolumn_pair[perturb_column_pair].op = op
                break
        htcolumn_pair[perturb_column_pair].isolatable = isolatable_score
    return htcolumn_pair

def col_equal_filter(data,lhs_cols,rhs_col,skip_rows=[]):
    # return bool 
    exist_equal_col = 1
    isequal = [0 for _ in range(len(lhs_cols))]
    for n in range(len(data)):
        if n in skip_rows:
            continue
        elements = [data[col][n] for col in lhs_cols]
        rhs = data[rhs_col][n]
        for i in range(len(elements)):
            if math.isclose(elements[i],rhs):
                isequal[i] += 1
            
        if (n-len(skip_rows)-max(isequal)) > (len(data)-len(skip_rows))*0.05:
            exist_equal_col = 0
            break
        
    return(exist_equal_col)

def stability_test(data,col_pair,allow_rate,rel_ce,abs_ce,skip_rows,violation_rows):
    stability = 1
    # max_th1 = ht1
    volation_count = len(violation_rows)
    if len(col_pair) == 3:
        for new_cols_combination in itertools.combinations(col_pair,2):
            artype,ardict,other_violation_rows = ar_tools.op_discover(data,new_cols_combination,allow_rate,rel_ce,abs_ce,skip_rows)
            if artype == 'negative':
                continue
            if  len(other_violation_rows) <= volation_count:
                # ht1 = -ht1
                stability = 0
                break
                
    elif len(col_pair) == 4:
        # first traversal 3 cols relationships
        for new_cols_combination in itertools.combinations(col_pair,3):
            artype,ardict,other_violation_rows = ar_tools.op_discover(data,new_cols_combination,allow_rate,rel_ce,abs_ce,skip_rows)
            if artype == 'negative':
                continue
            # If there is a relationship that requires fewer columns and haves fewer violations, stability = 0, ht1 = -ht1 
            if  len(other_violation_rows) <= volation_count:
                # ht1 = -ht1
                stability = 0
                break
            # else:
            #     another_ht1 = calculated_score(data,new_cols_combination,skip_rows)
            #     max_th1 = max(max_th1,another_ht1) 
        if stability == 1:
            # then traversal 2 cols relationships
            for new_cols_combination in itertools.combinations(col_pair,2):
                artype,ardict,other_violation_rows = ar_tools.op_discover(data,new_cols_combination,allow_rate,rel_ce,abs_ce,skip_rows)
                if artype == 'negative':
                    continue
                if len(other_violation_rows) <= volation_count:
                    # ht1 = -ht1
                    stability = 0
                    break 
                # else:
                #     another_ht1 = calculated_score(data,new_cols_combination,skip_rows)
                #     max_th1 = max(max_th1,another_ht1)
    # if stability == 1 and ht1_update == 1:
    #     ht1 = max_th1
    return(stability)

def formula_test(data,col_pair,col_formula,violation_rows,allviolation_rows_index,sample_type,allow_rate,rel_ce,abs_ce,skip_rows):
    col_number = len(col_pair)
    for n in range(len(data)):
        if n in skip_rows:
            continue
        col_val = [data[col_pair[i]][n] for i in range(col_number)]
        token,col_val = allnum(col_val)
        if token == 0:
            violation_rows[n] = col_val
            allviolation_rows_index.append(n)
            continue
        try:
            if sample_type == 'P':
                lhs_values = ar_tools.formual_value(col_formula,0,col_val[:3],[])
            else:
                lhs_values = ar_tools.formual_value(col_formula,0,col_val[:3],col_pair)
            # if math.isclose(lhs_values,col_val[-1],rel_tol=ce) == False and math.isclose(lhs_values,col_val[-1],abs_tol=ce) == False:
            if math.isclose(lhs_values,col_val[-1],rel_tol=rel_ce) == False or math.isclose(lhs_values,col_val[-1],abs_tol=abs_ce) == False:
                violation_rows[n] = col_val
                allviolation_rows_index.append(n)
        except ZeroDivisionError:
            violation_rows[n] = col_val
            allviolation_rows_index.append(n)
            
        if len(violation_rows.keys())/(len(data)-len(skip_rows)) > allow_rate:
            ishold = 0
            break
        
def formula_get(_formulas,traversal_n,col_number,sample_type):
    if sample_type == 'P':
        col_formula = _formulas['col_formula'][traversal_n]
    else:
        if  col_number == 3:
            # col_formula = ''
            col_formula = '{c}={a}{op1}{b}'.format(
                a = _formulas['lhs_col_one'][traversal_n],b = _formulas['lhs_col_two'][traversal_n],
                c = _formulas['rhs_col'][traversal_n],
                op1 = _formulas['op'][traversal_n]
                )
            
        else:
            col_formula = '{d}=({a}{op1}{b}){op2}{c}'.format(
                a = _formulas['lhs_col_one'][traversal_n],b = _formulas['lhs_col_two'][traversal_n],
                c = _formulas['lhs_col_three'][traversal_n],d = _formulas['rhs_col'][traversal_n],
                op1 = _formulas['op1'][traversal_n],op2 = _formulas['op2'][traversal_n]
                )
    return col_formula
    
def verification_relationhip(sample_type,traversal_n,_formulas,data,col_pair,ops,allow_rate,rel_ce,abs_ce,skip_rows=[],col_number=3):
    violation_rows = {}
    ishold = 1
    skip_rows = []
    allviolation_rows_index = []
    # abs_ce = 1e-07
    
    col_formula = formula_get(_formulas,traversal_n,col_number,sample_type)
        
    if col_number == 3:
        # if sample_type == 'N':
            # return(ishold,violation_rows,col_formula,skip_rows)
        
        for n in range(len(data)):
            if n in skip_rows:
                continue
            col_val = [data[col_pair[i]][n] for i in range(col_number)]
            token,col_val = allnum(col_val)
            if token == 0:
                continue
            op = ops
            try:
                lhs = eval(f"{col_val[0]}{op}{col_val[1]}")
                rhs = col_val[2]
                # if math.isclose(lhs,rhs,rel_tol=ce)==False and math.isclose(lhs,rhs,abs_tol=ce)==False:
                if math.isclose(lhs,rhs,rel_tol=rel_ce)==False or math.isclose(lhs,rhs,abs_tol=abs_ce)==False:
                    violation_rows[n] = col_val
                    allviolation_rows_index.append(n)
            except ZeroDivisionError:
                violation_rows[n] = col_val
                allviolation_rows_index.append(n)
            except:
                print('math.isclose error',n)
            if len(violation_rows.keys())/(len(data)-len(skip_rows)) > allow_rate:
                ishold = 0
                break
    else:
        for n in range(len(data)):
            if n in skip_rows:
                continue
            col_val = [data[col_pair[i]][n] for i in range(col_number)]
            token,col_val = allnum(col_val)
            if token == 0:
                violation_rows[n] = col_val
                allviolation_rows_index.append(n)
                continue
            try:
                if sample_type == 'P':
                    lhs_values = ar_tools.formual_value(col_formula,0,col_val[:3],[])
                else:
                    lhs_values = ar_tools.formual_value(col_formula,0,col_val[:3],col_pair)
                if math.isclose(lhs_values,col_val[-1],rel_tol=rel_ce) == False or math.isclose(lhs_values,col_val[-1],abs_tol=abs_ce) == False:
                    violation_rows[n] = col_val
                    allviolation_rows_index.append(n)
            except ZeroDivisionError:
                violation_rows[n] = col_val
                allviolation_rows_index.append(n)
                
            if len(violation_rows.keys())/(len(data)-len(skip_rows)) > allow_rate:
                ishold = 0
                break
                
            # return(ishold,violation_rows,lhs_cols,rhs_col,ops)
    allviolation_rows_index = list(set(allviolation_rows_index+skip_rows))
    return(ishold,violation_rows,col_formula,allviolation_rows_index)

def formula_restore(col_list,ops):
    if len(col_list) == 3:
        col_formula = '{c}={a}{op1}{b}'.format(
            a = col_list[0], b = col_list[1], c = col_list[2],
            op1 = ops[0]
            )
    elif len(col_list) == 4:
        col_formula = '{d}=({a}{op1}{b}){op2}{c}'.format(
            a = col_list[0], b = col_list[1],
            c = col_list[2], d = col_list[3],
            op1 = ops[0], op2 = ops[1]
            )
    return col_formula


def add_ardict(ardict,formula_tuple):
    if formula_tuple not in ardict.keys():
        ardict[formula_tuple] = 1
    else:
        ardict[formula_tuple] += 1
    return ardict
    
def add_violation_row(violation_rows,formula_tuple,row_n):
    if formula_tuple in violation_rows.keys():
        violation_rows[formula_tuple].append(row_n)
    else:
        violation_rows[formula_tuple] = []
        violation_rows[formula_tuple].append(row_n)
    return violation_rows


def has_subformula(K_comb,subformula_col_pool):
    for subformula_col in subformula_col_pool:
        if len(K_comb) == len(subformula_col):
            continue
        
        col_overlap = 0
        for col in subformula_col:
            if col in K_comb:
                col_overlap += 1
        if col_overlap == len(subformula_col):
            return True
    return False

def binomial_allow_rate_main(binomial_upper_bound:dict,formula_tuple:tuple,iswork:bool):
    if formula_tuple not in binomial_upper_bound.keys():
        if iswork:
            binomial_upper_bound[formula_tuple] = {'ns':1,'n':1,'upper_bound':0}
        else:
            binomial_upper_bound[formula_tuple] = {'ns':0,'n':1,'upper_bound':0}
        
        # if formula_tuple == ((0, 1), 2, '-'):
        #     print(binomial_upper_bound[formula_tuple])
    else:
        if iswork:
            binomial_upper_bound[formula_tuple]['ns'] += 1
        binomial_upper_bound[formula_tuple]['n'] += 1
    
    return binomial_upper_bound