import pandas as pd
import os
import json
import time
################################
import sys

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'auto_relate'))
sys.path.insert(0, parent_dir)

import formula_analyze
import data_processing
import hypothesis_testing2
import ht_compute
import optimization_flags
import optimization_stats
################################

################################

def skip_case_collect(big_case_path, cols:int):
    big_case = pd.DataFrame(pd.read_csv(big_case_path))
    case_skip = set(big_case[big_case['cols']>cols]['case_id'])
    return case_skip

def single_formula_test(cols:set,gt_df:pd.DataFrame):
    for n in range(len(gt_df)):
        if gt_df['col4'][n] != gt_df['col4'][n]:
            formula_cols = {gt_df['col1'][n],gt_df['col2'][n],gt_df['col3'][n]}
        else:
            formula_cols = {gt_df['col1'][n],gt_df['col2'][n],gt_df['col3'][n],gt_df['col4'][n]}
            
        if cols == formula_cols:
            return gt_df['sample_type'][n]
            
    return 'nonentity'

def formulas_pr_statistics(formulas_dict:dict,gt_df:pd.DataFrame):
    postive_samples = len(gt_df[gt_df['sample_type']=='P'])
    tp = 0
    fp = 0 
    for formula_key in formulas_dict.keys():
        cols = set(formulas_dict[formula_key][1])
        stat_res = single_formula_test(cols,gt_df)
        
        if stat_res == 'P':
            tp += 1
        elif stat_res == 'N':
            fp += 1
            
    return(postive_samples,tp,fp)

#######################
# input:  test_type(clean or dirty), methods(['Auto-Relate']), type_constraint('')
# output: positive_num,tp_dict,fp_dict
# 
# other output: measure_result(res_save_path), time_record(time_record_path)
#######################

# should be
#######################
# input: dataset_path, data_type('clean_data' or 'dirty_data'), methods, result_save_head_path
# output: positive_num,tp_dict,fp_dict
#######################

def measure_and_save_result(dataset_path:str, data_type:str, methods:list, result_save_folder_path:str) -> None:
    big_case_path = os.path.join(dataset_path,'case_detail.csv')
    
    # path_complement
    case_id_list = os.listdir(dataset_path)
    case_skip = skip_case_collect(big_case_path,cols=20)
    
    _gt_name = 'ground_truth.csv'
    
    if data_type == 'clean_data':
        table_name = 'clean_data.csv'
        res_name = 'clean_data_result.csv'
        timing_name = 'clean_data_timing_log.csv'
        allow_rate = 0
    elif data_type == 'dirty_data':
        allow_rate = 0.2
        table_name = 'dirty_data_mix_0.1.csv'
        res_name = 'dirty_data_result.csv'
        timing_name = 'dirty_data_timing_log.csv'
    
    
    # create folder for method
    positive_num = 0
    tp_dict,fp_dict = {},{}
    for m in methods:
        
        result_save_subfolder = os.path.join(result_save_folder_path,m)
        
        if not os.path.exists(result_save_subfolder):
            os.makedirs(result_save_subfolder)
        
        tp_dict[m] = 0
        fp_dict[m] = 0
        res_save_path = os.path.join(result_save_folder_path,m,res_name)
        # Keep the header order aligned with the appended result rows below:
        # (case_id, formula, formula_type, score, variable_number, skip_rows)
        _title = [('case_id','formula','formula_type','score','variable_number','skip_rows')]

        pd.DataFrame(_title).to_csv(res_save_path,header=False,index=False)

        if m == 'Auto-Relate':
            timing_path = os.path.join(result_save_folder_path,m,timing_name)
            timing_title = [(
                'case_id',
                'data_type',
                'formula',
                'formula_type',
                'score',
                'rows',
                'table_cols',
                'variable_number',
                'skip_rows_count',
                'verification_runtime_seconds',
                'stability_result',
                'ht2_filtered',
                'ht_option',
                'disable_groupby_bound',
                'disable_closed_form',
                'disable_binomial_bound',
                'optimization_stats_delta_json',
            )]
            pd.DataFrame(timing_title).to_csv(timing_path,header=False,index=False)
    
    
    for case_id in case_id_list:
        
        data_folder_path = os.path.join(dataset_path,case_id)
        
        if case_id in case_skip or os.path.isdir(data_folder_path) == False:
            continue
        
        try:
            data_path = os.path.join(dataset_path,case_id,table_name)
            data = pd.DataFrame(pd.read_csv(data_path))
            numerical_columns = data_processing.discover_numerical_columns(data)
            # print(case_id,' rows:',len(data),' cols:',len(data.columns))
        except:
            pass
            
        
        _gt_path = os.path.join(dataset_path,case_id,_gt_name)
        if os.path.exists(_gt_path) == True:
            gt_df = pd.DataFrame(pd.read_csv(_gt_path))
            
            if 'Auto-Relate' in methods:
                positive_num,tp_dict,fp_dict = one_formula_test(case_id,data_type,data,gt_df,
                                                                res_name,allow_rate,
                                                                result_save_folder_path,
                                                                numerical_columns,
                                                                positive_num,tp_dict,fp_dict)
            
            
            filtered_methods = [method for method in methods if method != 'Auto-Relate']
            if filtered_methods != []:
                raise ValueError("This public release includes Auto-Relate only; comparison methods are not bundled.")
        
        
        # try:
        #     _gt_path = os.path.join(dataset_path,case_id,_gt_name)
        #     # os.path.exists(_gt_path)
        #     if os.path.exists(_gt_path) == True:
        #         gt_df = pd.DataFrame(pd.read_csv(_gt_path))
        #         positive_num,tp_dict,fp_dict = one_formula_test(case_id,data_type,data,gt_df,
        #                                                         res_name,allow_rate,
        #                                                         result_save_folder_path,
        #                                                         numerical_columns,positive_num,
        #                                                         tp_dict,fp_dict)
        #     else:
        #         # print('no gt')
        #         continue
        # except:
        #     pass
        
    return
        
        

def one_formula_test(case_id,test_type,data:pd.DataFrame,gt_df:pd.DataFrame,
                     res_name,allow_rate,save_head_path,
                     numerical_columns,positive_num,tp_dict,fp_dict,time_record_path=''):
        
    for n in range(len(gt_df)):
        
        if gt_df['col4'][n] != gt_df['col4'][n]:
            lhs_cols = (gt_df['col1'][n],gt_df['col2'][n])
            rhs_cols = gt_df['col3'][n]
            ops = [gt_df['op1'][n]]
        else:
            lhs_cols = (gt_df['col1'][n],gt_df['col2'][n],gt_df['col3'][n])
            rhs_cols = gt_df['col4'][n]
            ops = [gt_df['op1'][n],gt_df['op2'][n]]
        
        K_comb = tuple(list(lhs_cols)+[rhs_cols])
        
        formula = gt_df['formula'][n]
        formula_type = gt_df['sample_type'][n]
        
        if formula_type == 'P':
            positive_num += 1
        
        skip_rows = gt_df['violation'][n]
        if skip_rows == skip_rows and test_type == 'dirty_data':
            skip_rows = eval(skip_rows)
        else:
            skip_rows = []
        # skip_rows = []
        
        tp_dict,fp_dict = singe_formula_ht(case_id,data,formula,formula_type,K_comb,numerical_columns,
                                           ops,skip_rows,save_head_path,res_name,tp_dict,fp_dict,allow_rate)
        
    return(positive_num,tp_dict,fp_dict)
        
def singe_formula_ht(case_id,data,formula,formula_type,K_comb,numerical_columns,ops,skip_rows,
                     save_head_path,res_name,tp_dict,fp_dict,allow_rate):
    
    columns = K_comb
    col_number = len(K_comb)
    violation_rows = skip_rows
    threshold = 0.5
    p_threshold = 0.05
    # p_threshold = 0.001
    rel_ce,abs_ce = 1e-09,1e-09
    start = time.perf_counter()
    stats_before = optimization_stats.snapshot()
    stability = None
    ht2_filtered = False
    option_selection = ''
    
    stability = formula_analyze.stability_test(data,K_comb,allow_rate,rel_ce,abs_ce,[],violation_rows)
    
    if stability == 0:
        score = 1
    
    elif hypothesis_testing2.filter_by_P_value(data,numerical_columns,K_comb,violation_rows,p_threshold):
            # print(K_comb,'ht2 filter')
            ht2_filtered = True
            score = 1
    else:
        if col_number == 3:
            option_selection = 'single_perturb'
        elif col_number == 4:
            option_selection = 'bound_sample_skip'
        
        formula_eval = formula_analyze.formula_restore(columns,ops)
        score = ht_compute.run(data,formula_eval,option_selection,K_comb,ops,rel_ce,abs_ce,violation_rows)

    runtime_seconds = time.perf_counter() - start
    stats_after = optimization_stats.snapshot()
    stats_delta = {
        key: stats_after.get(key, 0.0) - stats_before.get(key, 0.0)
        for key in sorted(set(stats_before) | set(stats_after))
        if stats_after.get(key, 0.0) - stats_before.get(key, 0.0) != 0
    }
        
    row = [(case_id,formula,formula_type,score,col_number,skip_rows)]
    save_path = os.path.join(save_head_path,'Auto-Relate',res_name)
    pd.DataFrame(row).to_csv(save_path,mode='a',header=False,index=False) 

    timing_name = 'dirty_data_timing_log.csv' if res_name == 'dirty_data_result.csv' else 'clean_data_timing_log.csv'
    timing_path = os.path.join(save_head_path,'Auto-Relate',timing_name)
    timing_row = [(
        case_id,
        'dirty_data' if res_name == 'dirty_data_result.csv' else 'clean_data',
        formula,
        formula_type,
        score,
        len(data),
        len(data.columns),
        col_number,
        len(skip_rows),
        round(runtime_seconds, 6),
        stability,
        ht2_filtered,
        option_selection,
        optimization_flags.disable_groupby_bound(),
        optimization_flags.disable_closed_form(),
        optimization_flags.disable_binomial_bound(),
        json.dumps(stats_delta, sort_keys=True),
    )]
    pd.DataFrame(timing_row).to_csv(timing_path,mode='a',header=False,index=False)
    
    if score <= threshold:
        if formula_type == 'P':
            tp_dict['Auto-Relate'] += 1
        else:
            fp_dict['Auto-Relate'] += 1
            
    return(tp_dict,fp_dict)
