import ast
import hashlib
import pandas as pd
import numpy as np
import os
import sys

import ht_afd
import AFD_case_filter

import warnings
warnings.filterwarnings("ignore")


def _get_fd_sample_seed():
    seed = os.environ.get("AUTO_RELATE_FD_SAMPLE_SEED")
    if seed in (None, ""):
        return None
    return int(seed)


def _get_fd_ht2_threshold():
    value = os.environ.get("AUTO_RELATE_FD_HT2_THRESHOLD")
    if value in (None, ""):
        return 0.0001
    return float(value)


def _get_fd_violation_threshold():
    value = os.environ.get("AUTO_RELATE_FD_VIOLATION_THRESHOLD")
    if value in (None, ""):
        return 0.05
    return float(value)


def _stable_sample_state(base_seed, test_type, case_id, left_col, right_col, sample_type):
    if base_seed is None:
        return None

    seed_material = f"{base_seed}|{test_type}|{case_id}|{left_col}|{right_col}|{sample_type}"
    digest = hashlib.md5(seed_material.encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def _resume_enabled():
    return os.environ.get("AUTO_RELATE_FD_RESUME", "0") == "1"


def _load_processed_keys(res_path):
    if not _resume_enabled():
        return set()
    if not os.path.exists(res_path) or os.path.getsize(res_path) == 0:
        return set()

    try:
        df = pd.read_csv(res_path)
    except Exception:
        return set()

    required_cols = {"case_id", "left_col", "right_col", "sample_type"}
    if not required_cols.issubset(df.columns):
        return set()

    processed = set()
    for _, row in df.iterrows():
        processed.add(
            (
                str(row["case_id"]),
                str(row["left_col"]),
                str(row["right_col"]),
                str(row["sample_type"]),
            )
        )
    return processed

# head_path: the folder save test cases.
# test_type: clean_data or dirty data
# res_path: output directory + method name + result name
def batch_run(head_path:str,test_type:str,res_path:str)-> None:
    '''
    Input:
    head_path: the folder save test cases.
    test_type: clean_data or dirty_data.
    res_path: output directory + method name + result name.
    Output:
    None
    '''
    
    _title = [('case_id','left_col','right_col','sample_type','score','ht2',
               'orgin_hold_rate','violation_row_index','violation_example')]
    if not (_resume_enabled() and os.path.exists(res_path) and os.path.getsize(res_path) > 0):
        pd.DataFrame(_title).to_csv(res_path,header=False,index=False)
    processed_keys = _load_processed_keys(res_path)
    base_sample_seed = _get_fd_sample_seed()
    violation_threshold = _get_fd_violation_threshold()
    ht2_threshold = _get_fd_ht2_threshold()
    
    
    if test_type == 'clean_data':
        case_name = 'clean_data'
    elif test_type == 'dirty_data':
        case_name = 'dirty_data_mix_0.1'
    
    cases_list = sorted(
        case_id for case_id in os.listdir(head_path)
        if os.path.isdir(os.path.join(head_path, case_id))
    )
    for case_id in cases_list:
        # case_id = cases_list[0]
        # case_id = '270342562'
        formula_path = os.path.join(head_path, case_id, 'ground_truth.csv')
        # original_test_data_path = os.path.join(head_path, case_id, 'data', 'clean.csv')
        # case_path = os.path.join(head_path, case_id, 'data', 'clean_data.csv')
        
        original_test_data_path = os.path.join(head_path, case_id, '{}.csv'.format(case_name))
        # original_test_data_path = os.path.join(head_path, case_id, 'data', '{}.csv'.format(case_name))
        # case_path = os.path.join(head_path, case_id, 'data', '{}.csv'.format(test_type))
        
        
        # if os.path.exists(case_path) == False:
        if os.path.exists(original_test_data_path) == False:
            print(case_id, 'not exist')
            continue
        else:
            original_test_data = pd.DataFrame(pd.read_csv(original_test_data_path))
            # case_df = pd.DataFrame(pd.read_csv(case_path, dtype=str, keep_default_na=False))
            # case_df = pd.DataFrame(pd.read_csv(original_test_data_path, dtype=str, keep_default_na=False))
            
            # if len(case_df) < len(original_test_data)//2:
            #     continue
            
            gt_df = pd.DataFrame(pd.read_csv(formula_path))
            
            
            # if len(case_df) > 100:
            #     case_df = case_df.sample(n=100,axis=0)
            #     case_df = case_df.reset_index(drop=True) 
            
            
            for n in range(len(gt_df)):
                
                case_df = pd.DataFrame(pd.read_csv(original_test_data_path, dtype=str, keep_default_na=False))
                
                
                left_col = gt_df['left_col'][n]
                right_col = gt_df['right_col'][n]
                sample_type = gt_df['sample_type'][n]
                key = (str(case_id), str(left_col), str(right_col), str(sample_type))
                if key in processed_keys:
                    continue
                violation_row_index = ast.literal_eval(gt_df['violation_rows'][n])
                # violation_row_index = []
                # violation_row_index = gt_df['violation_rows'][n]
                violation_example = gt_df['violation_sample'][n]
            
            
                if (sample_type == 'N' and 
                    (AFD_case_filter.violation_rate(original_test_data,violation_row_index,violation_threshold) 
                    or AFD_case_filter.numeric_type(original_test_data,left_col,right_col))):
                    continue
                
                # if (AFD_case_filter.violation_rate(original_test_data,violation_row_index,violation_threshold) 
                #     or AFD_case_filter.numeric_type(original_test_data,left_col,right_col)) :
                #     continue
            
                if test_type == 'clean_data':
                    use_ht2 = False
                    case_df = case_df.drop(violation_row_index)
                    case_df = case_df.reset_index(drop=True)
                else:
                    use_ht2 = True
                    # use_ht2 = False
            
                if len(case_df) > 10000:
                    sample_state = _stable_sample_state(base_sample_seed, test_type, case_id,
                                                        left_col, right_col, sample_type)
                    case_df = case_df.sample(n=10000, axis=0, random_state=sample_state)
                    case_df = case_df.reset_index(drop=True) 


            
                ht_afd.one_formula_test(use_ht2,ht2_threshold,case_id,case_df,left_col,right_col,
                                        sample_type,violation_row_index,violation_example,res_path)
                processed_keys.add(key)
        
                # try:
                #     ht_afd.one_formula_test(use_ht2,ht2_threshold,case_id,case_df,left_col,right_col,
                #                             sample_type,violation_row_index,violation_example,res_path)
                # except:
                #     print(n)
                #     print(case_id)
                    
