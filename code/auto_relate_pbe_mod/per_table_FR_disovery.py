
import os
import sys
import pandas as pd
import hypothesis_testing1_pbe
import hypothesis_testing2

##############################################

class String_Formula():
    def __init__(self, input_cols, output_col, pbe_res=None):
        self.pbe_res = pbe_res
        self.input_cols = input_cols
        self.output_col = output_col
        

def pbe_discover(case_path,pbe_file_api,case_columns,allow_rate):
    pbe_formula_dict = {}
    ##############################
    # s_minComplianceRatio = 1
    s_minComplianceRatio = min(0.99,allow_rate)
    maxReadRecordCnt = 10000000
    maxLeftMostColCnt = 50
    hasHeader = True
    pbe_results = pbe_file_api.ProcessOneCSV(case_path, s_minComplianceRatio, 
                                             maxReadRecordCnt, maxLeftMostColCnt, 
                                             hasHeader)
    
    for res in pbe_results:
        # res.Print()
        if res.complianceRatio < allow_rate:
            continue
        
        input_cols = [case_columns[i] for i in res.actuallyUsedInputColsIdxInOrigTable]
        input_cols = list(set(input_cols))
        
        if len(input_cols) == 0:
            continue
        
        output_col = case_columns[res.outputColIdxInOrigTable]
        
        pbe_formula_dict[output_col] = String_Formula(input_cols, output_col, res)
        
    return pbe_formula_dict


def ht1_calculate(pbe_row_api,case_df,input_cols,output_col,pbe_formula):
    has_upper_bound = 1
    subset_length = 'random'
    score,bound = hypothesis_testing1_pbe.bound_sample_pbe(pbe_row_api,has_upper_bound,case_df,input_cols,
                                                           output_col,pbe_formula,subset_length,[])
    return(score,bound)

def ht2_calculate(case_df,total_cols,formula_cols,violation_rows,p_threshold):
    
    # if use_ht2 == True and len(violation_row_index) != 0:
    #     formula_cols = input_cols + [output_col]
    #     ht2_filter, ht2_score = hypothesis_testing2.get_ht2_score(case_df, case_columns, formula_cols, 
    #                                                               violation_row_index, ht2_threshold)

    #     if ht2_filter == True:
    #         score, bound = 1, 'HT2'
    #         row = [(case_id,input_cols,output_col,sample_type,score,bound,ht2_score,
    #                 orgin_hold_rate,violation_row_index,violation_example)]
    #         file_operation.res_save(row,res_save_path)
    #         return
        
    # else:
    #     ht2_score = ''
    
    
    score = hypothesis_testing2.filter_by_P_value(case_df, total_cols, formula_cols, violation_rows, p_threshold)
    
    return(score)
    

def batch_ht1_calculate(pbe_row_api, pbe_formula_dict, case_df, ht1_threshold):
    
    formula_dict = {}
    
    for formula_key in pbe_formula_dict.keys():
        
        res = pbe_formula_dict[formula_key]
        
        pbe_formula = res.pbe_res
        input_cols, output_col = res.input_cols, res.output_col
        
        try:
            score, bound = ht1_calculate(pbe_row_api, case_df, input_cols, output_col, pbe_formula)
        except:
            print('ht1_calculate error:', formula_key)
        
        if score > ht1_threshold:
            continue
            
        formula_dict[output_col] = String_Formula(input_cols, output_col, res)
        formula_dict[output_col].score = score
        formula_dict[output_col].bound = bound
        
    return formula_dict
    

def table_test(case_path, allow_rate, pbe_file_api, pbe_row_api):
    
    # pbe_file_api, pbe_row_api = load_pbe_dll()
    
    case_df = pd.DataFrame(pd.read_csv(case_path, dtype=str, keep_default_na=False))
    case_columns = case_df.columns.tolist()
    
    ################## pbe part
    
    pbe_formula_dict = pbe_discover(case_path,pbe_file_api,case_columns,allow_rate)
    
    ################## ht part
    
    
    
    ht1_threshold = 0.5
    formula_dict = batch_ht1_calculate(pbe_row_api, pbe_formula_dict, case_df, ht1_threshold)
    
    return formula_dict
    
