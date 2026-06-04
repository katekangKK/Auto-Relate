
# ht1-pbe
import random
import sys
import os


parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'auto_relate'))
sys.path.insert(0, parent_dir)

import hypothesis_testing1
import data_processing
import optimization_flags



###################### pbe part
from runtime_loader import ensure_clr_loaded, load_pbe_apis

_, List = ensure_clr_loaded()



def load_pbe_dll():
    pbe_file_api, pbe_row_api, dll_count = load_pbe_apis(__file__)
    print('successfully loaded # of DLLs: ', dll_count)
    return pbe_file_api, pbe_row_api

## convert python list to csharp list, which is necessary to call C# library from python
def convert_python_list_to_csharp_list(python_list):
    # Create a .NET List from a Python list
    csharp_list = List[str]()  # Creating a .NET List of strings
    for py_string in python_list:
        csharp_list.Add(py_string)

    return csharp_list

###################### ht1 part
def sample_optimized(pbe_row_api,has_upper_bound,data,input_cols,output_col,
                     pbe_formula,subset_length,bound_test_frequency,skip_rows):
    
    # pbe_file_api, pbe_row_api = load_pbe_dll()
    legal_rows = []
    bound = 0
    
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
    
    sucess_number = 0
    for n in range(sample_number):
        
        if n in bound_test_station:
            # print(sucess_number,n-sucess_number)
            lower_bound,upper_bound = hypothesis_testing1.wilson_interval(sucess_number,n)
            if not optimization_flags.disable_binomial_bound() and lower_bound >= 0.5:
                return(sucess_number/n,2)
            elif not optimization_flags.disable_binomial_bound() and has_upper_bound == True and upper_bound < 0.5:
                return(sucess_number/n,3)
            
        
        current_row = random.choice(legal_rows)
        perturb_row = random.choice(legal_rows)
        
        while perturb_row == current_row:
            perturb_row = random.choice(legal_rows)
        
        orig_one_table_row = list(data.iloc[current_row])
        orig_one_table_row = [str(i) for i in orig_one_table_row]
        
        
        all_cols = input_cols + [output_col]
        # There is difference between 'random.choice' and 'random.sample'.
        if subset_length == 'random':
            # subset_length = random.randint(1,2)
            if len(all_cols) <= 3:
                subset_length = 1
            else:
                subset_length = random.choice([i for i in range(1,len(all_cols)//2)])
        perturb_cols = random.sample(all_cols,subset_length)
        
        perturbed_one_table_row = perturb_single_row(data,perturb_cols,input_cols,perturb_row,orig_one_table_row)
        
        # convert orig_one_table_row and perturbed_one_table_row, into C# lists
        # orig_one_table_row_csharp = convert_python_list_to_csharp_list(orig_one_table_row)
        # perturbed_one_table_row = ['A.', 'TMDS2_DATA1-', '9']
        perturbed_one_table_row = [i.strip() for i in perturbed_one_table_row]
        perturbed_one_table_row_csharp = convert_python_list_to_csharp_list(perturbed_one_table_row)
        
        perturb_output = pbe_row_api.RunResultProgramOneRow(pbe_formula, perturbed_one_table_row_csharp)
        # pbe_formula.Print()
        
        # output_col = 'AX'
        if output_col in perturb_cols:
            origal_output = str(data[output_col][perturb_row]).strip() 
        else:
            origal_output = str(data[output_col][current_row]).strip() 
        
        if origal_output == perturb_output:
            sucess_number += 1

    ht1 = sucess_number/sample_number
    
    return(ht1,bound)

def perturb_single_row(data,perturb_cols,input_cols,perturb_row,orig_one_table_row):
    
    perturbed_one_table_row = orig_one_table_row
    
    for col in perturb_cols:
        if col in input_cols:
            col_index = list(data.columns).index(col)
            perturbed_one_table_row[col_index] = data[col][perturb_row]
    

    perturbed_one_table_row = [str(item) for item in perturbed_one_table_row]
    
    return perturbed_one_table_row

########################## the group-by bound
def multicolumns_partition(data,columns,skip_rows):
    
    null_partition_dict,partition_pool = data_processing.partition_analyze(columns,2)
    
    partition_dict = data_processing.partition(data,null_partition_dict,partition_pool,skip_rows)
    
    htscore, row_num = [], len(data)-len(skip_rows)
    for perturb_column_pair in partition_dict.keys():
        pdict = partition_dict[perturb_column_pair]
        htscore.append(hypothesis_testing1.perturb_score(pdict,row_num))
    return(sum(htscore)/len(htscore))


# version0: without the group-by bound
# def bound_sample_pbe(pbe_row_api,has_upper_bound,data,input_cols,output_col,pbe_formula,subset_length,skip_rows):
    
#     ###################### wihtout  the first bound
#     bound_test_frequency = 100
#     ht1,bound = sample_optimized(pbe_row_api,has_upper_bound,data,input_cols,output_col,
#                                  pbe_formula,subset_length,bound_test_frequency,skip_rows)
    
#     return(ht1,bound)

# data = tem_df
# skip_rows = []
def bound_sample_pbe(pbe_row_api,has_upper_bound,data,input_cols,output_col,pbe_formula,subset_length,skip_rows):
    columns = input_cols + [output_col]
    if not optimization_flags.disable_groupby_bound():
        partition_lower_bound = multicolumns_partition(data,columns,skip_rows)
        # print(subset_length)
        if partition_lower_bound >= 0.5:
            return(partition_lower_bound,1)
    
    
    bound_test_frequency = 100
    ht1,bound = sample_optimized(pbe_row_api,has_upper_bound,data,input_cols,output_col,
                                 pbe_formula,subset_length,bound_test_frequency,skip_rows)
    
    return(ht1,bound)
