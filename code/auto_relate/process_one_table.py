import class_create
import pandas as pd
import table_formulas_discovery
import data_processing
import ht_program_disvoery

# def run(max_violation_rate,data_path,degree_of_parallelism):
    
#     data = pd.DataFrame(pd.read_csv(data_path))
#     numerical_columns = data_processing.discover_numerical_columns(data)
#     rel_ce,abs_ce = 1e-09,1e-09
    
#     formulas_dict,running_type = table_formulas_discovery.formulas_discover_together_multiprocessing_easy_dirty('test_case',data,numerical_columns,
#                                                                                max_violation_rate,rel_ce,abs_ce,degree_of_parallelism)
    
    
#     # if len(formulas_dict.keys()) == 0:
#     #     print('No mathematical formula has been discovered.')
        
#     # else:
#     #     print('The mathematical formulas found are as follows: ')
#     #     for formula in formulas_dict.keys():
#     #         res = class_create.AutoRelate_Result(formula,formulas_dict[formula][0],formulas_dict[formula][1])
#     #         res.Print()
    
#     formulas = []
#     for formula in formulas_dict.keys():
#         res = class_create.AutoRelate_Result(formula,formulas_dict[formula][0],formulas_dict[formula][1])
#         formulas.append(res)
    
#     return formulas


def arithmetic_run(max_columns_number,max_violation_rate,data_path,degree_of_parallelism,
                   col_relationship=True,row_relationship=False):
    
    # data_path = 'transposed_data.csv'
    data = pd.DataFrame(pd.read_csv(data_path))
    formulas = []
    
    if col_relationship == True:
        numerical_columns = data_processing.discover_numerical_columns(data)
        rel_ce,abs_ce = 1e-09,1e-09
        
        formulas_dict,running_type = table_formulas_discovery.run(max_columns_number,data,numerical_columns,max_violation_rate,
                                                                  rel_ce,abs_ce,degree_of_parallelism)
    
        for formula in formulas_dict.keys():
            res = class_create.AutoRelate_Result(formula,formulas_dict[formula][0],formulas_dict[formula][1])
            formulas.append(res)
    
    
    if row_relationship == True:
        data_transposed = data.transpose()
        data_transposed.columns = ['row_{}'.format(i) for i in range(len(data_transposed.columns))]
        numerical_columns = data_processing.discover_numerical_columns(data_transposed)
        rel_ce,abs_ce = 1e-09,1e-09
        
        formulas_dict,running_type = table_formulas_discovery.run(max_columns_number,data_transposed,numerical_columns,
                                                                  max_violation_rate,rel_ce,abs_ce,degree_of_parallelism)
    
        for formula in formulas_dict.keys():
            res = class_create.AutoRelate_Result(formula,formulas_dict[formula][0],formulas_dict[formula][1])
            formulas.append(res)
    
    
    return formulas
        
def program_run(max_violation_rate,data_path,program_discovery,col_relationship=True,row_relationship=False):
    
    data = pd.DataFrame(pd.read_csv(data_path))
    formulas = []
    
    use_ht2 = True
    ht1_threshold, ht2_threshold = 0.5, 0.05
    ce = 0.01
    
    
    if col_relationship == True:
        numerical_columns = data_processing.discover_numerical_columns(data)
        
        for agg_feature in program_discovery:        
            program_dict = ht_program_disvoery.program_discovery_and_ht_test(agg_feature,data,numerical_columns,use_ht2,
                                                                             ht1_threshold,ht2_threshold,max_violation_rate,ce)
            
            for program_key in program_dict:
                col_start, col_end, col_program = program_key
                ht1_score = program_dict[program_key]
                res = class_create.AutoRelate_Program_Result(agg_feature, ht1_score, col_start, col_end, col_program)
                formulas.append(res)    
    
    if row_relationship == True:
        data = data.apply(pd.to_numeric, errors='coerce')
        data_transposed = data.transpose()
        data_transposed.columns = ['row_{}'.format(i) for i in range(len(data_transposed.columns))]
        numerical_columns = data_processing.discover_numerical_columns(data_transposed)
        
        for agg_feature in program_discovery:        
            program_dict = ht_program_disvoery.program_discovery_and_ht_test(agg_feature,data_transposed,numerical_columns,use_ht2,
                                                                             ht1_threshold,ht2_threshold,max_violation_rate,ce)
            
            for program_key in program_dict:
                col_start, col_end, col_program = program_key
                ht1_score = program_dict[program_key]
                res = class_create.AutoRelate_Program_Result(agg_feature, ht1_score, col_start, col_end, col_program)
                formulas.append(res)  
    
    return formulas
        


def run(max_violation_rate,data_path,degree_of_parallelism,
        arithmetic_discovery=False,program_discovery=False,
        col_relationship=True,row_relationship=False):


    if arithmetic_discovery != False:
        arithmetic_formulas = arithmetic_run(arithmetic_discovery,max_violation_rate,data_path,
                                             degree_of_parallelism,col_relationship,row_relationship)
    else:
        arithmetic_formulas = []
    
    
    if program_discovery != False:
        program_formulas = program_run(max_violation_rate,data_path,program_discovery,
                                       col_relationship,row_relationship)
    else:
        program_formulas = []

    return(arithmetic_formulas,program_formulas)

