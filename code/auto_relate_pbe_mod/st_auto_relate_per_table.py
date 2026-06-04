
import ast
import os
import time
import pandas as pd
import numpy as np
import sys
import per_table_FR_disovery
from runtime_loader import ensure_clr_loaded, load_pbe_apis


##############################################
_, _ = ensure_clr_loaded()

def load_pbe_dll():
    pbe_file_api, pbe_row_api, dll_count = load_pbe_apis(__file__)
    print('successfully loaded # of DLLs: ', dll_count)
    return pbe_file_api, pbe_row_api
##############################################

def get_detail(gt_df, target_input_cols, target_output_col):
    for n in range(len(gt_df)):
        input_cols = ast.literal_eval(gt_df['input_cols'][n])
        output_col = gt_df['output_col'][n]
        
        if set(input_cols) == set(target_input_cols) and output_col == target_output_col:
            sample_type, hold_rate  = gt_df['sample_type'][n], gt_df['hold_rate'][n]
            violation_row_index, violation_example = gt_df['violation_row_index'][n], gt_df['violation_example'][n]
            return([sample_type, hold_rate, violation_row_index, violation_example])

    return([None for i in range(4)])

def run(test_type, head_path, save_head_path):
    gt_name = '_ground_truth.csv'
    
    if test_type == 'clean_data':
        allow_rate = 1
        table_name = 'clean_data.csv'
        time_record_name = 'clean_time_record.csv'
        save_path = os.path.join(save_head_path,'clean_data_per_table.csv')
    else:
        allow_rate = 0.7
        # table_name = 'dirty_data.csv'
        table_name = 'dirty_data_mix_percent10.csv'
        time_record_name = 'dirty_time_record.csv'
        save_path = os.path.join(save_head_path,'dirty_data_per_table.csv')
    
    save_title = [('case_id','input_cols','output_col','sample_type','HT1','bound','HT2',
                   'rows','cols','hold_rate','violation_row_index','violation_example')]
    pd.DataFrame(save_title).to_csv(save_path,index=False,header=False)
    
    time_record_title = [('case_id','rows','cols','time')]
    time_record_path = os.path.join(save_head_path,time_record_name)
    pd.DataFrame(time_record_title).to_csv(time_record_path,index=False,header=False)
    
    pbe_file_api, pbe_row_api = load_pbe_dll()
    
    case_id_list = os.listdir(head_path)
    for case_id in case_id_list:
        # case_id = case_id_list[0]
        case_time_start = time.perf_counter()
        
        gt_path = os.path.join(head_path,case_id,gt_name)
        case_path = os.path.join(head_path,case_id,table_name)
        
        formula_dict = per_table_FR_disovery.table_test(case_path, allow_rate, pbe_file_api, pbe_row_api)
        
        gt_df = pd.DataFrame(pd.read_csv(gt_path))
        case_df = pd.DataFrame(pd.read_csv(case_path, dtype=str, keep_default_na=False))
        rows_num = len(case_df)
        cols_num = len(case_df.columns)
        
        for output_col in formula_dict.keys():
            input_cols = formula_dict[output_col].input_cols
            ht1_score = formula_dict[output_col].score
            ht1_bound = formula_dict[output_col].bound
            
            [sample_type, hold_rate, violation_row_index, violation_example] = get_detail(gt_df, input_cols, output_col)

            if sample_type == None:
                continue
            
            if test_type == 'clean_data':
                ht2_score = ''
            else:
                ht2_score = formula_dict[output_col].ht2_score
            
            
            save_row = [(case_id, input_cols, output_col, sample_type, ht1_score, ht1_bound, ht2_score, 
                         rows_num, cols_num, hold_rate, violation_row_index, violation_example)]
            pd.DataFrame(save_row).to_csv(save_path,mode='a',header=False,index=False) 


        case_time_finish = time.perf_counter()
        time_row = [(case_id, rows_num, cols_num, round(case_time_finish-case_time_start,2))] 
        pd.DataFrame(time_row).to_csv(time_record_path, mode='a', header=False, index=False) 


# case_id = 'table_242210___xlsx_00768d1a18878884697cceeb545832e2b8096f07.xlsx___line_1'
