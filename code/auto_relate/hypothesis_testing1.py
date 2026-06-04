
import random
import math
import re

################################
import data_processing
import ar_tools
import ht_single_perturb
import optimization_flags
import optimization_stats


def _compile_formula_evaluator(formula, columns):
    rhs = formula.split('=', 1)[1].strip()
    expression = rhs
    # Replace column names with positional placeholders without relying on
    # the string layout assumptions inside ar_tools.formual_parse.
    for index, column in sorted(enumerate(columns[:-1]), key=lambda item: len(item[1]), reverse=True):
        pattern = r'(?<![A-Za-z0-9_])' + re.escape(column) + r'(?![A-Za-z0-9_])'
        expression = re.sub(pattern, f'__vals[{index}]', expression)
    return compile(expression, '<auto_relate_formula>', 'eval')


def _formula_holds(formula_code, row_values, rel_ce, abs_ce):
    try:
        lhs = eval(formula_code, {"__builtins__": {}}, {"__vals": row_values[:-1]})
    except ZeroDivisionError:
        return False
    rhs = row_values[-1]
    return math.isclose(lhs, rhs, rel_tol=rel_ce) or math.isclose(lhs, rhs, abs_tol=abs_ce)


def wilson_interval(ns,n,z = 1.96):
    # alpha defaults 0.05
    # confidence interval 95% 0.475
    # z = 1.96
    # confidence interval 80% 0.4
    # z = 1.28
    
    nf = n - ns
    mid_value = (ns+0.5*z**2)/(n+z**2)
    error_bound = (z/(n+z**2))*math.sqrt((ns*nf/n)+z**2/4)
    upper_bound = mid_value + error_bound
    lower_bound = mid_value - error_bound
    return(lower_bound,upper_bound)

def perturb_score(pdict,row_num,skip_num=0):
    numerator = 0
    row_num -= skip_num
    for key in pdict.keys():
        key_num = len(pdict[key])
        # count = (row_num-key_num)/row_num
        count = (key_num-1)/(row_num-1)
        numerator += count*key_num
        # print(key,numerator/denominator)
    score = numerator/row_num
    return score


def navie_sample(data,columns,subset_length:str,formula,rel_ce,abs_ce,skip_rows):          
    col_number = len(columns)
    legal_rows = []
    
    _formula_str = ar_tools.formual_parse(formula,columns)
    
    if subset_length != 'random':
        print('subset_length error')
        return
    
    for n in range(len(data)):
        if n in skip_rows:
            continue
        legal_rows.append(n)
        
    rows = len(legal_rows)
    if rows == 1:
        print('len(legal_rows) == 1')
        return
    
    sample_number = min(100*rows,10000)
    optimization_stats.incr("naive_sample_calls")
    optimization_stats.incr("naive_sample_trials", sample_number)
    
    sucess_number = 0
    for _ in range(sample_number):
        current_row = random.choice(legal_rows)
        perturb_row = random.choice(legal_rows)
        
        while perturb_row == current_row:
            perturb_row = random.choice(legal_rows)
        
        # There is difference between 'random.choice' and 'random.sample'.
        subset_length = random.choice([1,2])
        perturb_cols = random.sample(columns,subset_length)
        
        row_values = []
        for i in range(col_number):
            if columns[i] in perturb_cols:
                row_values.append(data[columns[i]][perturb_row])
            else:
                row_values.append(data[columns[i]][current_row])
                
        row_values = data_processing.nan_tf_zero(row_values)
        if ar_tools.formual_verification(_formula_str,row_values,rel_ce,abs_ce) == True:
            sucess_number += 1

    ht1 = sucess_number/sample_number
    return ht1


def singlecol_sample(data,columns,formula,rel_ce,abs_ce,skip_rows):
    col_number = len(columns)
    legal_rows = []
    formula_code = _compile_formula_evaluator(formula, columns)

    for n in range(len(data)):
        if n in skip_rows:
            continue
        legal_rows.append(n)

    rows = len(legal_rows)
    if rows == 1:
        print('len(legal_rows) == 1')
        return

    sample_number = min(100 * rows, 10000)
    optimization_stats.incr("singlecol_fallback_calls")
    optimization_stats.incr("singlecol_fallback_trials", sample_number)

    sucess_number = 0
    for _ in range(sample_number):
        current_row = random.choice(legal_rows)
        perturb_row = random.choice(legal_rows)

        while perturb_row == current_row:
            perturb_row = random.choice(legal_rows)

        perturb_col = random.choice(columns)

        row_values = []
        for i in range(col_number):
            if columns[i] == perturb_col:
                row_values.append(data[columns[i]][perturb_row])
            else:
                row_values.append(data[columns[i]][current_row])

        row_values = data_processing.nan_tf_zero(row_values)
        if _formula_holds(formula_code, row_values, rel_ce, abs_ce) == True:
            sucess_number += 1

    ht1 = sucess_number / sample_number
    return ht1


def multicolumns_partition(data,columns,skip_rows):
    
    null_partition_dict,partition_pool = data_processing.partition_analyze(columns,2)
    
    partition_dict = data_processing.partition(data,null_partition_dict,partition_pool,skip_rows)
    
    htscore, row_num = [], len(data)-len(skip_rows)
    for perturb_column_pair in partition_dict.keys():
        pdict = partition_dict[perturb_column_pair]
        htscore.append(perturb_score(pdict,row_num))
    return(sum(htscore)/len(htscore))

def sample_optimized(has_upper_bound,data,columns,subset_length,formula,rel_ce,abs_ce,skip_rows,bound_test_frequency):          
    col_number = len(columns)
    legal_rows = []
    bound = 0
    _formula_str = ar_tools.formual_parse(formula,columns)
    
    for n in range(len(data)):
        if n in skip_rows:
            continue
        legal_rows.append(n)
        
    rows = len(legal_rows)
    if rows == 1:
        print('len(legal_rows) == 1')
        return
    
    sample_number = min(100*rows,10000)
    bound_test_station = [bound_test_frequency*i for i in range(1,sample_number//100)]
    optimization_stats.incr("multicol_sample_calls")
    optimization_stats.incr("multicol_sample_trials_budget", sample_number)
    
    sucess_number = 0
    for n in range(sample_number):
        optimization_stats.incr("multicol_sample_trials_executed")
        if optimization_flags.disable_binomial_bound() == False and n in bound_test_station:
            optimization_stats.incr("binomial_bound_checks")
            # print(sucess_number,n-sucess_number)
            lower_bound,upper_bound = wilson_interval(sucess_number,n)
            if lower_bound >= 0.5:
                optimization_stats.incr("binomial_early_stop_accept")
                return(sucess_number/n,2)
            elif has_upper_bound == 1 and upper_bound < 0.5:
                optimization_stats.incr("binomial_early_stop_reject")
                return(sucess_number/n,3)
                
        current_row = random.choice(legal_rows)
        perturb_row = random.choice(legal_rows)
        
        while perturb_row == current_row:
            perturb_row = random.choice(legal_rows)
        
        # There is difference between 'random.choice' and 'random.sample'.
        perturb_cols = random.sample(columns,subset_length)
        
        row_values = []
        for i in range(col_number):
            if columns[i] in perturb_cols:
                row_values.append(data[columns[i]][perturb_row])
            else:
                row_values.append(data[columns[i]][current_row])
                
        row_values = data_processing.nan_tf_zero(row_values)
        if ar_tools.formual_verification(_formula_str,row_values,rel_ce,abs_ce) == True:
            sucess_number += 1

    ht1 = sucess_number/sample_number
    return(ht1,bound)

def multi_sample(has_upper_bound,data,columns,subset_length:int,formula,rel_ce,abs_ce,skip_rows):
    optimization_stats.incr("groupby_bound_calls")
    if optimization_flags.disable_groupby_bound():
        optimization_stats.incr("groupby_bound_disabled_calls")
        partition_lower_bound = 0
    else:
        partition_lower_bound = multicolumns_partition(data,columns,skip_rows)
    bound = 0
    # print(subset_length)
    if partition_lower_bound >= 0.5:
        optimization_stats.incr("groupby_early_rejects")
        return(partition_lower_bound,1)
    
    bound_test_frequency = 100
    ht1,bound = sample_optimized(has_upper_bound,data,columns,subset_length,formula,rel_ce,abs_ce,skip_rows,bound_test_frequency)
    # print(ht1)
    ht1 = max(ht1,partition_lower_bound)
    return(ht1,bound)

def bound_sample(has_upper_bound,data,columns,subset_length:str,formula,rel_ce,abs_ce,skip_rows,Dict=None,Dict_num=None,ops=None):
    # print(subset_length)
    if subset_length != 'random':
        print('subset_length error')
        return
    
    if optimization_flags.disable_closed_form():
        optimization_stats.incr("closed_form_disabled_calls")
        ht1_singlecol = singlecol_sample(data, columns, formula, rel_ce, abs_ce, skip_rows)
    else:
        optimization_stats.incr("closed_form_used_calls")
        ht1_singlecol = ht_single_perturb.run(Dict,Dict_num,len(data)-len(skip_rows),len(columns),ops)
    # print(ht1_singlecol)
    ht1_multcols,bound = multi_sample(has_upper_bound,data,columns,2,formula,rel_ce,abs_ce,skip_rows)
    # print(ht1_multcols,bound)
    ht1 = (ht1_singlecol+ht1_multcols)/2
    # ht1 = ht1_multcols
    return(ht1,bound)

# def bound_only_once(data,columns,subset_length,formula,ce,skip_rows):
#     partition_lower_bound = multicolumns_partition(data,columns,skip_rows)
#     if partition_lower_bound >= 0.5:
#         return partition_lower_bound
#     ht1 = navie_sample(data,columns,subset_length,formula,ce,skip_rows)
#     return ht1
    
    
