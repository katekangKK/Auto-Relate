
import itertools
import multiprocessing

################################
import ar_tools
import op_discovery
import formula_analyze
import ht_compute
import hypothesis_testing2
################################


# def formulas_discover_together_multiprocessing_easy_dirty(case_id,data,numerical_columns,
#                                                     max_violation_rate,rel_ce,abs_ce,process_num=30):
def run(max_col_num,data,numerical_columns,max_violation_rate,rel_ce,abs_ce,process_num=30):
    subformula_col_pool = []
    ht1_threshold = 0.5
    threshold = ht1_threshold
    p_threshold = 0.05
    formulas_dict = {}
    
    if len(numerical_columns) < 3:
        return formulas_dict,'insufficient numerical columns'
    elif len(numerical_columns) > 50:
        numerical_columns = numerical_columns[:50]
    
    if len(data) < 100:
        data_type = 'little data'
    else:
        data_type = 'big data'
        data = data.sample(n=100,axis=0)
        data = data.reset_index(drop=True) 
    
    zero_cols,zero_index = zero_cols_get(data,numerical_columns)
    numerical_columns_without_zero = list(set(numerical_columns) - set(zero_cols))
    # print(len(numerical_columns_without_zero))
    
    K = 2
    for K_comb in itertools.combinations(numerical_columns_without_zero,K):
        if has_binary_relation(data,K_comb,max_violation_rate,rel_ce,abs_ce):
            subformula_col_pool.append(K_comb)
            
    K_comb_list = []
    
    if max_col_num == 3:
        col_num = [3]
    elif max_col_num == 4:
        col_num = [3,4]
        
    for K in col_num:
        K_comb_listall = [K_comb for K_comb in itertools.combinations(numerical_columns_without_zero,K)]
        for K_comb in K_comb_listall:
            if formula_analyze.has_subformula(K_comb,subformula_col_pool) == False:
                K_comb_list.append(K_comb)
    
    running_type = 'single'
    if (len(K_comb_list) < 1000 and data_type == 'little data') or (len(K_comb_list) < 600 and data_type == 'big data') or (process_num<=1) :
        # print(case_id,len(K_comb_list),running_type)
        formulas_dict,subformula_col_pool = single_mining_together(data,data_type,numerical_columns,
                                                                    K_comb_list,
                                                                    max_violation_rate,
                                                                    rel_ce,abs_ce,
                                                                    threshold,p_threshold,
                                                                    subformula_col_pool,formulas_dict)
    
    elif __name__ == 'table_formulas_discovery':
        running_type = 'multi'
        # print(case_id,len(K_comb_list),running_type)
        process_num = min(process_num,len(K_comb_list))
        
        # try:
        formulas_dict,subformula_col_pool = multi_mining_together(data,data_type,numerical_columns,
                                                                    K_comb_list,process_num,
                                                                    max_violation_rate,
                                                                    rel_ce,abs_ce,
                                                                    threshold,p_threshold,
                                                                    formulas_dict,subformula_col_pool)
        # except:
        #     print('multi_mining_together error')

    formulas_dict,subformula_col_pool = subformula_test(formulas_dict,subformula_col_pool)
    
    return formulas_dict,running_type

######################################################################################################## 

def has_binary_relation(data,cols_combination,max_violation_rate,rel_ce,abs_ce):
    artype,ardict,violation_rows = ar_tools.op_discover(data,cols_combination,max_violation_rate,rel_ce,abs_ce)
    if artype == 'negative':
        return False
    else:
        return True
    

def zero_cols_get(data,numerical_columns):
    zero_cols = []
    zero_index = {}
    for col in numerical_columns:
        zero_index[col] = set(data[data[col]==0].index)
        if len(data[data[col]==0]) == len(data):
            zero_cols.append(col)
    return zero_cols,zero_index


def single_mining_together(data,data_type,numerical_columns,
                            K_comb_list,max_violation_rate,
                            rel_ce,abs_ce,
                            threshold,p_threshold,
                            subformula_col_pool,formulas_dict):
    
    for K_comb in K_comb_list:
        formulas_dict,subformula_col_pool = single_mining(data,data_type,numerical_columns,
                                                            K_comb,len(K_comb),
                                                            max_violation_rate,
                                                            rel_ce,abs_ce,
                                                            threshold,p_threshold,
                                                            subformula_col_pool,formulas_dict)
    
    return(formulas_dict,subformula_col_pool)

def single_mining(data,data_type,numerical_columns,
                    K_comb,K,
                    max_violation_rate,
                    rel_ce,abs_ce,
                    threshold,p_threshold,
                    subformula_col_pool,formulas_dict):
    
    
    artype,ardict,violation_rows = op_discovery.np_op_discover(data,K_comb,max_violation_rate,rel_ce,abs_ce,data_type)
    if artype != 'negative':
        # print(artype)
        formula,option_selection,columns,ops = formula_analyze.dissect(K,K_comb,artype,data,violation_rows)
        # print(formula)
        if hypothesis_testing2.filter_by_P_value(data,numerical_columns,K_comb,violation_rows,p_threshold):
            # print(K_comb,'ht2 filter')
            return(formulas_dict,subformula_col_pool)
        subformula_col_pool.append(K_comb)
        HT_score = ht_compute.run(data,formula,option_selection,columns,ops,rel_ce,abs_ce,violation_rows)
        if HT_score <= threshold:
            formulas_dict[formula] = [HT_score,columns]
        # else:
        #     print(K_comb,'ht1 filter')
    return(formulas_dict,subformula_col_pool)


def multi_mining_together(data,data_type,numerical_columns,
                            K_comb_list,process_num,
                            max_violation_rate,
                            rel_ce,abs_ce,
                            threshold,p_threshold,
                            formulas_dict,subformula_col_pool):
    
    pool = multiprocessing.Pool(process_num)
    M =  multiprocessing.Manager()
    res_queue = M.Queue()
    subformula_queque = M.Queue()
    args_list = []
    for K_comb in K_comb_list:
        # origin
        args_list.append((data,data_type,numerical_columns,
                            K_comb,len(K_comb),
                            max_violation_rate,rel_ce,abs_ce,
                            threshold,p_threshold,
                            res_queue,subformula_queque))
        
    pool.starmap(op_discovery.op_discover_batch, args_list)
    
    pool.close()
    pool.join()
    
    while res_queue.empty() == False:
        formula,HT_score,columns = res_queue.get()
        formulas_dict[formula] = [HT_score,columns]
         
         
    while subformula_queque.empty() == False:
        comb = subformula_queque.get()
        subformula_col_pool.append(comb)
        
    return(formulas_dict,subformula_col_pool)



def subformula_test(formulas_dict,subformula_col_pool):
    overlapped_formulas = []
    for formula in formulas_dict:
        formula_cols = formulas_dict[formula][1] 
        if formula_analyze.has_subformula(formula_cols,subformula_col_pool):
            overlapped_formulas.append(formula)
    
    for false_formula in overlapped_formulas:
        formulas_dict.pop(false_formula)
    
    return(formulas_dict,subformula_col_pool)

######################################################################################
