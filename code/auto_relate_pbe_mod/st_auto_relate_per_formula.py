
import ast
import pandas as pd
import numpy as np
import os
import sys
import ht_pbe
from runtime_loader import ensure_clr_loaded, load_pbe_apis

############################## pbe part
_, _ = ensure_clr_loaded()


def dirty_allow_rate():
    value = os.environ.get("AUTO_RELATE_ST_ALLOW_RATE")
    if value in (None, ""):
        return 0.7
    return float(value)


def load_pbe_dll():
    pbe_file_api, pbe_row_api, dll_count = load_pbe_apis(__file__)
    print('successfully loaded # of DLLs: ', dll_count)
    return pbe_file_api, pbe_row_api
############################################

# group_number,total_gp = 29,30
# res_cover=False
def batch_test(test_type,gt_file_path,case_head_path,save_head_path,
               res_cover=False,group_number=False,total_gp=False):

    ###################### load ground_truth csv
    
    gt_df = pd.DataFrame(pd.read_csv(gt_file_path))
    
    ######################
    
    positive_num = 0
    # ht2_threshold = 0.001
    # no HT2
    ht2_threshold = 0.0000001
    
    if test_type == 'clean_data':
        use_ht2 = False
        allow_rate = 1
        table_name = 'clean_data.csv'
        res_name = 'clean_data_result.csv'
    else:
        use_ht2 = True
        # use_ht2 = False
        allow_rate = dirty_allow_rate()
        table_name = 'dirty_data_mix_0.1.csv'
        res_name = 'dirty_data_result.csv'
    
    
    parallel_tem_file_folder = os.path.join(save_head_path,'Auto-Relate','parallel_tem_file')
    if not os.path.exists(parallel_tem_file_folder):
        os.makedirs(parallel_tem_file_folder)
        
        
    ###################### initialize result csv
    if group_number == False and total_gp == False:
        res_save_path = os.path.join(save_head_path,'Auto-Relate',res_name)
        tem_path = os.path.join(save_head_path,'Auto-Relate','tem_file.csv')
        
    else:
        res_name = '{}.csv'.format(group_number)
        res_save_path = os.path.join(save_head_path,'Auto-Relate','parallel_formula',res_name)
        tem_path = os.path.join(save_head_path,'Auto-Relate','parallel_tem_file','{}.csv'.format(group_number))
        
        
        ###################### gt_df divide
        if len(gt_df)%total_gp == 0:
            group_capacity = len(gt_df)//total_gp
        else:
            group_capacity = len(gt_df)//total_gp+1
            
        gt_df = gt_df.iloc[group_capacity*group_number:min(group_capacity*(group_number+1),len(gt_df))]
        gt_df = gt_df.reset_index(drop=True)
    
    
    _title = [('case_id','input_cols','output_col','sample_type','score','bound','ht2',
               'orgin_hold_rate','violation_row_index','violation_example')]
    
    
    if not os.path.exists(res_save_path):
        pd.DataFrame(_title).to_csv(res_save_path,header=False,index=False)
    elif res_cover == True:
        pd.DataFrame(_title).to_csv(res_save_path,header=False,index=False)
        
    
    ###################### loading pbe
    
    pbe_file_api,pbe_row_api = load_pbe_dll()
    
    ##################################
    for n in range(len(gt_df)):
        case_id = gt_df['case_id'][n]
        input_cols = ast.literal_eval(gt_df['input_cols'][n])
        input_cols = list(set(input_cols))
        output_col = gt_df['output_col'][n]
        sample_type = gt_df['sample_type'][n]
        
        if sample_type == 'P':
            positive_num += 1
            # violation_row_index,violation_example = '',''
            orgin_hold_rate = 1
        else:
            # violation_row_index = ast.literal_eval(gt_df['violation_row_index'][n])
            # violation_example = gt_df['violation_example'][n]
            orgin_hold_rate = gt_df['hold_rate'][n]

        try:
            case_path = os.path.join(case_head_path,case_id,table_name)
            case_df = pd.DataFrame(pd.read_csv(case_path, dtype=str, keep_default_na=False))
        except:
            print(n,case_id)
            continue
        
        if len(case_df) < 5:
            print(n,'too little case',case_id)
            continue
        
        
        try:
            ht_pbe.compute_ht_score_and_save(use_ht2,ht2_threshold,pbe_file_api,allow_rate,pbe_row_api,res_save_path,
                                             case_path,case_id,sample_type,save_head_path,res_name,
                                             case_df,input_cols,output_col,tem_path,orgin_hold_rate)
        except:
            print(case_id)
            # error_row = [(case_id,n,'ht_pbe')]
            # pd.DataFrame(error_row).to_csv(error_case_path,mode='a',header=False,index=False)
    return







