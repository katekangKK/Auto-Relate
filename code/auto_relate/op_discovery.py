import itertools
import numpy as np
import math
#################################
import formula_analyze
import ht_compute
import hypothesis_testing2


#############################################################################
# np_op_discover

def np_op_discover(data,col_pair,allow_rate,rel_ce,abs_ce,data_type):
    check_step = [0,len(data)]
    split_num = 1
    ardict = {}
    violation_rows = {}  
    for i in range(split_num):
        data_split = data[check_step[i]:check_step[i+1]]
        # print(check_step[i],check_step[i+1])
        artype,ardict,violation_rows = np_op_discover_split(ardict,violation_rows,data_split,col_pair,
                                                            allow_rate,rel_ce,abs_ce,len(data),data_type)
        if artype == 'negative':
            break
        
        
    return(artype,ardict,violation_rows[artype])


def np_op_discover_split(ardict,violation_rows,data,col_pair,allow_rate,rel_ce,abs_ce,total_len,data_type):
    # ardict = {}
    # violation_rows = {}    
    # data_type = 'little data'
    col_number = len(col_pair)
    col_positions = set([i for i in range(col_number)])
    filter_num,formula_num = 0,0
    for lhs in itertools.permutations(col_positions,col_number-1):
        rhs, = list(col_positions - set(lhs))
        
        if col_number == 3:
            if data_type == 'little data':
                artype,ardict,violation_rows = np_op_three_cols_search(data,col_pair,lhs,rhs,ardict,violation_rows,
                                                                       allow_rate,rel_ce,abs_ce,total_len)
            else:
                artype,ardict,violation_rows = np_op_three_cols_search_bound(data,col_pair,lhs,rhs,ardict,violation_rows,
                                                                             allow_rate,rel_ce,abs_ce,total_len)
        elif col_number == 4:
            if data_type == 'little data':
                artype,ardict,violation_rows = np_op_four_cols_search(data,col_pair,lhs,rhs,ardict,violation_rows,allow_rate,
                                                                      rel_ce,abs_ce,total_len)
            else:
                artype,ardict,violation_rows = np_op_four_cols_search_bound(data,col_pair,lhs,rhs,ardict,violation_rows,allow_rate,
                                                                            rel_ce,abs_ce,total_len)
                
        if artype != 'negative':
            break
    
    violation_rows['negative'] = []
    return(artype,ardict,violation_rows)


def np_op_three_cols_search(data,col_pair,lhs,rhs,ardict,violation_rows,
                            allow_rate,rel_ce,abs_ce,total_len):
    
    col_one = np.array(data[col_pair[lhs[0]]])
    col_two = np.array(data[col_pair[lhs[1]]])
    rhs_col = np.array(data[col_pair[rhs]])
    
    for op1, in itertools.product(['+','*']):
        formula_tuple = (lhs,rhs,op1)
        # if formula_tuple in violation_rows.keys() and len(violation_rows[formula_tuple]) > total_len*allow_rate:
        #     continue
        
        np_col = single_col_np_tf(col_one,col_two,op1)  
        ardict,violation_rows = np_op_test(ardict,violation_rows,np_col,rhs_col,formula_tuple,
                                           allow_rate,rel_ce,abs_ce,total_len)
    
    artype = max(ardict,key=ardict.get)
    
    if len(violation_rows[artype]) > total_len*allow_rate:
    # if len(violation_rows[artype]) > total_len*allow_rate or bound_token == 'lower':
        artype = 'negative'
    
    return(artype,ardict,violation_rows)


def np_op_four_cols_search(data,col_pair,lhs,rhs,ardict,violation_rows,
                           allow_rate,rel_ce,abs_ce,total_len):
    
    col_one = np.array(data[col_pair[lhs[0]]])
    col_two = np.array(data[col_pair[lhs[1]]])
    col_three = np.array(data[col_pair[lhs[2]]])
    rhs_col = np.array(data[col_pair[rhs]])
    
    for op1 in ['+', '-', '*', '/']:
        for op2 in ['+', '-', '*', '/']:
            formula_tuple = (lhs,rhs,op1,op2)
            np_col = single_col_np_tf(col_one,col_two,op1)
            np_col = single_col_np_tf(np_col,col_three,op2)
            ardict,violation_rows = np_op_test(ardict,violation_rows,np_col,rhs_col,formula_tuple,
                                               allow_rate,rel_ce,abs_ce,total_len)
    
    artype = max(ardict,key=ardict.get)
    if len(violation_rows[artype]) > total_len*allow_rate:
        artype = 'negative'
    
    return(artype,ardict,violation_rows)        



def np_op_three_cols_search_bound(data,col_pair,lhs,rhs,ardict,violation_rows,
                                  allow_rate,rel_ce,abs_ce,total_len):
    
    col_one = np.array(data[col_pair[lhs[0]]])
    col_two = np.array(data[col_pair[lhs[1]]])
    rhs_col = np.array(data[col_pair[rhs]])
    
    if total_len < 100:
        max_error_num = total_len*allow_rate
    else:
        max_error_num = 26
    
    for op1, in itertools.product(['+','*']):
        formula_tuple = (lhs,rhs,op1)
        
        np_col = single_col_np_tf(col_one,col_two,op1)  
        ardict,violation_rows = np_op_test_bound(ardict,violation_rows,np_col,rhs_col,formula_tuple,
                                                 allow_rate,rel_ce,abs_ce,total_len)
    
    artype = max(ardict,key=ardict.get)
    
    if len(violation_rows[artype]) > max_error_num:
        artype = 'negative'
    
    return(artype,ardict,violation_rows)


def np_op_four_cols_search_bound(data,col_pair,lhs,rhs,ardict,violation_rows,allow_rate,rel_ce,abs_ce,total_len):
    col_one = np.array(data[col_pair[lhs[0]]])
    col_two = np.array(data[col_pair[lhs[1]]])
    col_three = np.array(data[col_pair[lhs[2]]])
    rhs_col = np.array(data[col_pair[rhs]])
    
    if total_len < 100:
        max_error_num = total_len*allow_rate
    else:
        max_error_num = 26
    
    for op1 in ['+', '-', '*', '/']:
        for op2 in ['+', '-', '*', '/']:
            formula_tuple = (lhs,rhs,op1,op2)
            np_col = single_col_np_tf(col_one,col_two,op1)
            np_col = single_col_np_tf(np_col,col_three,op2)
            # test
            ardict,violation_rows = np_op_test_bound(ardict,violation_rows,np_col,rhs_col,formula_tuple,
                                                     allow_rate,rel_ce,abs_ce,total_len)
    
    artype = max(ardict,key=ardict.get)
    if len(violation_rows[artype]) > max_error_num:
    # if len(violation_rows[artype]) > total_len*allow_rate or bound_token == 'lower':
        artype = 'negative'
    
    return(artype,ardict,violation_rows)    


def single_col_np_tf(col_one,col_two,op):
    if op == '+':
        np_col = np.add(col_one,col_two)
    elif op == '-':
        np_col = np.subtract(col_one,col_two) 
    elif op == '*':
        np_col = np.multiply(col_one,col_two) 
    elif op == '/':
        np_col = np.divide(col_one,col_two) 
    return np_col


def np_op_test(ardict,violation_rows,np_col,rhs_col,formula_tuple,allow_rate,rel_ce,abs_ce,total_len):
    if formula_tuple not in ardict.keys():
        ardict[formula_tuple] = 0
    if formula_tuple not in violation_rows.keys():
        violation_rows[formula_tuple] = []
    
    for n in range(len(np_col)):
        if (math.isclose(np_col[n],rhs_col[n],rel_tol=rel_ce) == True 
            and math.isclose(np_col[n],rhs_col[n],abs_tol=abs_ce) == True):
            ardict = formula_analyze.add_ardict(ardict,formula_tuple)
        else:
            violation_rows = formula_analyze.add_violation_row(violation_rows,formula_tuple,n)
            
        # if len(violation_rows[formula_tuple]) > split_num*len(np_col)*allow_rate:
        if len(violation_rows[formula_tuple]) > total_len*allow_rate:
            break

    return(ardict,violation_rows)


def np_op_test_bound(ardict,violation_rows,np_col,rhs_col,formula_tuple,allow_rate,rel_ce,abs_ce,total_len):
    if formula_tuple not in ardict.keys():
        ardict[formula_tuple] = 0
    if formula_tuple not in violation_rows.keys():
        violation_rows[formula_tuple] = []
    
    if total_len < 100:
        max_error_num = total_len*allow_rate
    else:
        max_error_num = 26
    
    for n in range(len(np_col)):
        if (math.isclose(np_col[n],rhs_col[n],rel_tol=rel_ce) == True 
            and math.isclose(np_col[n],rhs_col[n],abs_tol=abs_ce) == True):
            ardict = formula_analyze.add_ardict(ardict,formula_tuple)
        else:
            violation_rows = formula_analyze.add_violation_row(violation_rows,formula_tuple,n)
            
        # if len(violation_rows[formula_tuple]) > split_num*len(np_col)*allow_rate:
        if len(violation_rows[formula_tuple]) > max_error_num:
            break

    return(ardict,violation_rows)

#############################################################################

# op_discover_batch

def op_discover_batch(
        data,data_type,numerical_columns,
        K_comb,col_number,
        allow_rate,rel_ce,abs_ce,
        threshold,p_threshold,
        res_queue,subformula_col_pool_queque):
    
    artype,ardict,violation_rows = np_op_discover(data,K_comb,allow_rate,rel_ce,abs_ce,data_type)
    if artype != 'negative':
        if hypothesis_testing2.filter_by_P_value(data,numerical_columns,K_comb,violation_rows,p_threshold):
            return
        
        formula,option_selection,columns,ops = formula_analyze.dissect(col_number,K_comb,artype,data,violation_rows)
        
        subformula_col_pool_queque.put(tuple(columns),block=True)
        
        HT_score = ht_compute.run(data,formula,option_selection,columns,ops,rel_ce,abs_ce,violation_rows)
        
        if HT_score <= threshold:
            res_queue.put([formula,HT_score,columns],block=True)
            
    return