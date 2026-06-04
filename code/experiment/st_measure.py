import os
import sys

auto_relate_fd_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'auto_relate_pbe_mod'))
sys.path.insert(0, auto_relate_fd_dir)

import st_auto_relate_per_formula


def measure_and_save_result(dataset_path:str, data_type:str, methods:list, result_save_folder_path:str) -> None:
    
    for method in methods:
        
        result_save_subfolder = os.path.join(result_save_folder_path,method)
        
        if not os.path.exists(result_save_subfolder):
            os.makedirs(result_save_subfolder)
            
        parallel_result_subfolder = os.path.join(result_save_folder_path,method,'parallel_formula')
        
        if not os.path.exists(parallel_result_subfolder):
            os.makedirs(parallel_result_subfolder)
            

    res_name = '{}_result.csv'.format(data_type)
    
    if 'Auto-Relate' in methods:    
        
        res_path = os.path.join(result_save_folder_path, 'Auto-Relate', res_name)
        
        gt_file_path = os.path.join(dataset_path,'normal_formulas_P.csv')
        st_auto_relate_per_formula.batch_test(data_type,gt_file_path,dataset_path,result_save_folder_path,True)
        
        gt_file_path = os.path.join(dataset_path,'normal_formulas_N.csv')
        st_auto_relate_per_formula.batch_test(data_type,gt_file_path,dataset_path,result_save_folder_path,False)
        
    
    filtered_methods = [method for method in methods if method != 'Auto-Relate']
    
    if filtered_methods != []:
        raise ValueError("This public release includes Auto-Relate only; comparison methods are not bundled.")
    
    return
