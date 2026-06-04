
def run(dataset_path:str, data_type:str, test_type:str, methods:list, result_save_folder_path:str) -> None:

    if data_type == 'all':
        run(dataset_path,'clean_data',test_type,methods,result_save_folder_path)
        run(dataset_path,'dirty_data',test_type,methods,result_save_folder_path)
        return


    if test_type == 'AR':
        import ar_measure

        ar_measure.measure_and_save_result(dataset_path, data_type, methods, result_save_folder_path)
    elif test_type == 'ST':
        import st_measure

        st_measure.measure_and_save_result(dataset_path, data_type, methods, result_save_folder_path)
    elif test_type == 'FD':
        import fd_measure

        fd_measure.measure_and_save_result(dataset_path, data_type, methods, result_save_folder_path)
    
    else:
        print("Please select the correct test_type from 'AR, ST, FD'. ")
        
    return

