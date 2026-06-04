import itertools


def discover_numerical_columns(data):
    columns = data.columns.values.tolist()
    numerical_columns = []
    for column in columns:
        if data[column].dtype in ['int32','int64','float64']:
            numerical_columns.append(column)
    return(numerical_columns)



def nan_tf_zero(original_numerical_list):
    numerical_list = []
    for elem in original_numerical_list:
        if elem != elem:
            numerical_list.append(0)
        else:
            numerical_list.append(elem)
    return numerical_list


def partition(data,partition_dict,partition_pool,skip_rows):
    for row_index in range(len(data)):
        if row_index in skip_rows:
            continue
        
        row = data.iloc[row_index]
        for col_pair in partition_pool:
            partition_dict[col_pair] = pdict_add_row(partition_dict[col_pair],row_index,row,col_pair)
            
    return partition_dict


def partition_analyze(columns,length):
    null_partition_dict  = {}
    partition_pool,skip_pool = [],[]
    if length == 1:
        for col in columns:
            partition_pool[tuple(col)] = {}
            skip_pool.append(tuple(col))
        return(null_partition_dict,partition_pool)
    
    for perturb_column_pair in itertools.combinations(columns,length):
        if perturb_column_pair in skip_pool:
            continue
        
        null_partition_dict[perturb_column_pair] = {}
        partition_pool.append(perturb_column_pair)
        
        notperturb_column_pair = []
        for col in columns:
            if col not in perturb_column_pair:
                notperturb_column_pair.append(col)
        skip_pool.append(tuple(notperturb_column_pair))

    return(null_partition_dict,partition_pool)


def pdict_add_row(pdict,row_index,row,col_pair):
    # transform nan to 0
    key_pair = []
    for col in col_pair:
        if row[col] != row[col]:
            key_pair.append(0)
        else:
            key_pair.append(row[col])
    
    key_pair = tuple(key_pair)
    if key_pair not in pdict.keys():
        pdict[key_pair] = [row_index]
    else:
        pdict[key_pair] += [row_index]
    return pdict

