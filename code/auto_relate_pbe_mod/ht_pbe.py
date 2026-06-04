import pandas as pd
import sys
import os


##############################
import hypothesis_testing1_pbe

##############################
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'auto_relate'))
sys.path.insert(0, parent_dir)

import hypothesis_testing2
############################## pbe part
### The ST runner uses the bundled PBESynthesis DLLs under PythonDemo_AutoRelate/dlls.
proj_dir = sys.path[0]

def get_violation_row(res):
    violation_row_index = []
    for i in range(len(res.origOutputCol)):
        if  res.origOutputCol[i] != res.synthesizedOutputCol[i]:
            violation_row_index.append(i)
    return violation_row_index

def get_violation_example(res,violation_row_index):
    violation_example = []
    for i in range(len(violation_row_index)):
        if i >= 5:
            break
        row_index = violation_row_index[i]
        example_tuple = (res.origOutputCol[row_index],res.synthesizedOutputCol[row_index])
        violation_example.append(example_tuple)
    return violation_example
    
def include_index_col():
    value = os.environ.get("AUTO_RELATE_ST_INCLUDE_INDEX", "1").strip().lower()
    return value not in {"0", "false", "no", "off"}


def clean_fallback_enabled():
    value = os.environ.get("AUTO_RELATE_ST_CLEAN_FALLBACK", "0").strip().lower()
    return value in {"1", "true", "yes", "on"}


def find_pbe_formula(case_path,case_columns,target_input_cols,target_output_col,pbe_file_api,allow_rate):
    
    ############# find the pbe result
    s_minComplianceRatio = min(0.99,allow_rate)
    maxReadRecordCnt = 10000000
    maxLeftMostColCnt = 50
    hasHeader = True
    pbe_results = pbe_file_api.ProcessOneCSV(case_path, s_minComplianceRatio, maxReadRecordCnt, maxLeftMostColCnt, hasHeader)
    
    
    ############# check the pbe result
    pbe_formula = None
    violation_row_index = []
    violation_example = []
    for res_index in range(len(pbe_results)):
        
        res = pbe_results[res_index]
        # res.Print()
        # case_df = pd.DataFrame(pd.read_csv(case_path, dtype=str, keep_default_na=False))
        # case_columns = list(case_df.columns)
        # case_columns[res.outputColIdxInOrigTable]
        # [case_columns[i] for i in res.actuallyUsedInputColsIdxInOrigTable]
        input_cols = [case_columns[i] for i in res.actuallyUsedInputColsIdxInOrigTable]
        input_cols = list(set(input_cols))
        output_col = case_columns[res.outputColIdxInOrigTable]
        
        
        if output_col == target_output_col:
            
            if set(input_cols) == set(target_input_cols):
                pbe_formula = res
                violation_row_index = get_violation_row(res)
                violation_example = get_violation_example(res,violation_row_index)
                break
            else:
                print(input_cols)
                
    return(pbe_formula, violation_row_index, violation_example)

def string_len_filter(tem_file,max_string_len):
    columns = tem_file.columns.to_list()
    filter_token = False
    # col = columns[1]
    for col in columns:
        average_length = int(tem_file[col].astype(str).apply(len).mean())
        if average_length > max_string_len:
            filter_token = True
            break
    
    return filter_token
        
def compute_ht_score_and_save(use_ht2,ht2_threshold,pbe_file_api,allow_rate,pbe_row_api,res_save_path,
                              case_path,case_id,sample_type,save_head_path,res_name,
                              case_df,input_cols,output_col,tem_path,orgin_hold_rate):
    
    ##################
    case_columns = list(case_df.columns)
    case_columns_index = [case_columns.index(col) for col in input_cols] + [case_columns.index(output_col)]
    
    
    ################# find pbe methods
    # case_columns_index = ['A','B','C']
    tem_file = pd.read_csv(case_path, dtype = str, usecols=case_columns_index, keep_default_na=False)
    if include_index_col():
        tem_file['index']=[i for i in range(len(tem_file))]
    
    if string_len_filter(tem_file,100):
        print('string_len_filter')
        return
    
    tem_file.to_csv(tem_path, index=False)
    
    
    tem_case_columns = list(tem_file.columns)
    pbe_formula, violation_row_index, violation_example = find_pbe_formula(tem_path, tem_case_columns, input_cols, 
                                                                           output_col, pbe_file_api, allow_rate)
    formula_source = 'dirty'
    if pbe_formula == None and clean_fallback_enabled() and 'dirty_data' in os.path.basename(case_path):
        clean_case_path = os.path.join(os.path.dirname(case_path), 'clean_data.csv')
        if os.path.exists(clean_case_path):
            clean_tem_path = tem_path + '.clean.csv'
            clean_tem_file = pd.read_csv(clean_case_path, dtype=str, usecols=case_columns_index, keep_default_na=False)
            if include_index_col():
                clean_tem_file['index'] = [i for i in range(len(clean_tem_file))]
            if not string_len_filter(clean_tem_file, 100):
                clean_tem_file.to_csv(clean_tem_path, index=False)
                clean_case_columns = list(clean_tem_file.columns)
                pbe_formula, _, _ = find_pbe_formula(
                    clean_tem_path,
                    clean_case_columns,
                    input_cols,
                    output_col,
                    pbe_file_api,
                    allow_rate,
                )
                if pbe_formula != None:
                    formula_source = 'clean_fallback'
                    violation_row_index = []
                    violation_example = []
    
    
    ################# ht2
    if use_ht2 == True and len(violation_row_index) != 0:
        # total_cols = case_columns
        # violation_rows = violation_row_index
        # ht2_threshold = 0.05
        formula_cols = input_cols + [output_col]
        ht2_filter, ht2_score = hypothesis_testing2.get_ht2_score(case_df, case_columns, formula_cols, 
                                                                  violation_row_index, ht2_threshold)

        if ht2_filter == True:
            score, bound = 1, 'HT2'
            row = [(case_id,input_cols,output_col,sample_type,score,bound,ht2_score,
                    orgin_hold_rate,violation_row_index,violation_example)]
            # save_path = os.path.join(save_head_path,'HT',res_name)
            # file_operation.res_save(row,save_path)
            # file_operation.res_save(row,res_save_path)
            pd.DataFrame(row).to_csv(res_save_path,mode='a',header=False,index=False) 
            return
        
    else:
        ht2_score = ''
        
        
    ################# ht1
    if pbe_formula == None:
        score = 1
        bound = 'no_pbe_formula'
        print("no pbe formula found")
    else:
        ######################## heuristic
        # case_df_filter = case_df.drop(violation_row_index)
        # if len(set(case_df_filter[output_col])) <= 2:
        #     score, bound = 1, 'heuristic'
        #     row = [(case_id,input_cols,output_col,sample_type,score,bound,ht2_score,
        #             orgin_hold_rate,violation_row_index,violation_example)]
        #     save_path = os.path.join(save_head_path,'HT',res_name)
        #     file_operation.res_save(row,save_path)
        #     return
        
        
        has_upper_bound = 1
        subset_length = 'random'
        # score,bound = hypothesis_testing1_pbe.bound_sample_pbe(pbe_row_api,has_upper_bound,case_df,input_cols,
        #                                                        output_col,pbe_formula,subset_length,[])
        
        tem_df = pd.DataFrame(tem_file)
        score,bound = hypothesis_testing1_pbe.bound_sample_pbe(pbe_row_api,has_upper_bound,tem_df,input_cols,
                                                               output_col,pbe_formula,subset_length,violation_row_index)
        if formula_source == 'clean_fallback':
            bound = 'clean_fallback_{}'.format(bound)
    
    row = [(case_id,input_cols,output_col,sample_type,score,bound,ht2_score,
            orgin_hold_rate,violation_row_index,violation_example)]
    # save_path = os.path.join(save_head_path,'HT',res_name)
    # file_operation.res_save(row,save_path)
    # file_operation.res_save(row,res_save_path)
    pd.DataFrame(row).to_csv(res_save_path,mode='a',header=False,index=False) 
    return
