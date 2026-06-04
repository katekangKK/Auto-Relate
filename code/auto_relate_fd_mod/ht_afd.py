import pandas as pd
import sys
import os

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'auto_relate'))
sys.path.insert(0, parent_dir)

import hypothesis_testing2



def one_formula_test(use_ht2,ht2_threshold,case_id,case_df,left_col,right_col,sample_type,
                     violation_row_index,violation_example,res_save_path):
    
    rel_ce,abs_ce = 1e-09, 1e-09
    columns = [left_col,right_col]
    
    
    if use_ht2 == False:
        ht2_score = ''
        original_violation_rate = ''
    else:
        violation_rows = find_violations(case_df,left_col,right_col)
        case_columns = case_df.columns.tolist()
        formula_cols = [left_col,right_col]
        ht2_filter, ht2_score = hypothesis_testing2.get_ht2_score(case_df, case_columns, formula_cols, 
                                                                  violation_rows, ht2_threshold)

        original_violation_rate = round(len(violation_rows)/len(case_df),4)
        
        # if original_violation_rate < 0.05 or original_violation_rate > 0.5:
        #     return
        
        if ht2_filter == True or original_violation_rate > 0.5:
            score, bound = 1, 'HT2'
            original_violation_rate = ''
            row = [(case_id,left_col,right_col,sample_type,score,ht2_score,
                    original_violation_rate,violation_row_index,violation_example)]
            # file_operation.res_save(row,res_save_path)
            pd.DataFrame(row).to_csv(res_save_path,mode='a',header=False,index=False) 
            return
        
        
        case_df = case_df.drop(violation_rows)
        case_df = case_df.reset_index(drop=True)
        
        
    # score = ht_compute.run(case_df,'AFD','single_perturb',columns,'AFD',
    #                        rel_ce,abs_ce,violation_row_index)
    
    Dict,Dict_num,share_row = fd_dict_gen(case_df,columns)
    score = 1-HT1_FD(Dict,Dict_num)
    # Dict,Dict_num,share_row = fd_dict_gen(case_df,columns)
    # score = 1-HT1_FD(Dict,Dict_num)
    
    original_violation_rate = ''
    row = [(case_id,left_col,right_col,sample_type,score,ht2_score,
            original_violation_rate,violation_row_index,violation_example)]
    # file_operation.res_save(row,res_save_path)
    pd.DataFrame(row).to_csv(res_save_path,mode='a',header=False,index=False) 
    return

#########################form:

def find_violations(case_df, left_col, right_col):
    violations = []
    
    for key, grp in case_df.groupby(left_col):
        if len(grp[right_col].unique()) > 1:
            violations.append(grp[grp[right_col] != grp[right_col].mode()[0]])
    
    if violations:
        violation_df = pd.concat(violations)
        violation_rows = list(violation_df.index)
    else:
        violation_rows = []
        
    return violation_rows

def fd_dict_gen(df,col_pair):
    Dict = {}
    Dict_num = {}
    share_row = []
    for _ in range(len(df)):
        k = df[col_pair[0]][_]
        v = df[col_pair[1]][_]
        if pd.isnull(k) == False and pd.isnull(v) == False:
            k,v = str(k),str(v)
            share_row.append(_)
            if k not in Dict.keys():
                Dict[k],Dict_num[k] = [],[]
            if v not in Dict[k]:
                Dict[k].append(v) 
                Dict_num[k].append(1)
            else:
                Dict_num[k][Dict[k].index(v)] += 1
                
    return(Dict,Dict_num,share_row)


# Dict: A:a; B:b ...
# Dict: A:1; B:2 ...
def HT1_FD(Dict,Dict_num):
    ################Hypothesis testing1
    lk = []
    lv = []
    # count = 0
    for key in Dict.keys():
        for _ in range(Dict_num[key][0]):
            lk.append(key)
            lv.append(Dict[key][0]) 
    if len(lv) == 0:
        return 0
    ################        
    # for key in lk:
    #     if Dict_num[key][0] > 1:
    #         disturbance = random.choice(lv)
    #         if disturbance != Dict[key][0]:
    #             count += 1
    ################
    prob = 0
    for key in Dict_num.keys():
        if Dict_num[key][0] > 1:
            prob += (1 - lv.count(Dict[key][0])/len(lv))*Dict_num[key][0]
        else:
            prob += 0
    prob = prob/len(lv)
    return prob
