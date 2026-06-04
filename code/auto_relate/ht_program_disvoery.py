import numpy as np
import pandas as pd
import os
import itertools
import string
import random
import math
import ar_tools

import hypothesis_testing2

# This code contains multiple functions. I recommend starting with 'HT()' function.
# gen_ardict(), hypothesis_testing1(), hypothesis_testing2() are three important functions.
# Part of the code is more verbose but easier to understand, so I haven't changed there for now.

# Input: data,col_list,ce
# Output: isexist, start_col, end_col, agg_col, violation_row
# i is the index for 'start_col'
# j is the index for 'end_col'
# k is the index for 'agg_col'
# n is the nth row of data
########################################################################
def allnum(elements):
    token = 1
    new_elements = []
    for elem in elements:
        # To prevent overflow of int64 variables, numbers greater than the square root of the maximum value of int64 have been excluded.
        if np.issubdtype(type(elem),np.integer) == True:
            new_elements.append(elem)
        # float with 'nan', 'nan' will be transformed to 0
        elif np.issubdtype(type(elem),float) == True:
            if elem != elem:
                new_elements.append(0)
            else:
                new_elements.append(elem)
        else:
            token = 0
            new_elements = elements
            break
    return(token,new_elements)
    
def init_vcol_dict(col_list,i,j):
    violation_row,violation_row_number = {},{}
    for k in range(len(col_list)):
        if k < i or k > j:
            violation_row[k] = []
            violation_row_number[k] = []
    return(violation_row,violation_row_number)

def lhs_by_feature(agg_feature,lhs_list,max_col_dict,min_col_dict,ce):
    if agg_feature == 'sum':
        lhs = sum(lhs_list) 
    elif agg_feature == 'mean':
        lhs = np.mean(lhs_list)
    elif agg_feature == 'max':
        lhs = max(lhs_list)
        ce = 0
        max_col = lhs_list.index(max(lhs_list))
        if max_col in max_col_dict.keys():
            max_col_dict[max_col] += 1
        else:
            max_col_dict[max_col] = 1
    elif agg_feature == 'min':
        lhs = min(lhs_list)
        ce = 0
        min_col = lhs_list.index(max(lhs_list))
        if min_col in min_col_dict.keys():
            min_col_dict[min_col] += 1
        else:
            min_col_dict[min_col] = 1
    return(lhs,max_col_dict,min_col_dict,ce)

def check_equal(x,y,ce):
    if x != x:
        x =0
    if y != y:
        y =0
    if np.issubdtype(type(x),np.integer) == True and np.issubdtype(type(y),np.integer) == True:
        if x == y :
            return True
        else:
            return False
    elif x == 0 or y == 0:
        if x == y :
            return True
        else:
            return False
    elif np.issubdtype(type(x),float) == True or np.issubdtype(type(y),float) == True:
        if x/y >= (1-ce) and x/y <= (1+ce):
            return True
        else:
            return False
    else:
        return False

def find_rhs(agg_feature,data,col_list,violation_row,i,j,violation_row_number,nanskip_pool,allow_rate,ce):
    isexist = 1
    max_col_dict,min_col_dict = {},{}
    for n in range(len(data)):
        # really sum_value
        lhs_list = [data[col_list[col_index]][n] for col_index in range(i,j+1)]
        allnum_token,lhs_list = allnum(lhs_list)
        if allnum_token == 1:
            lhs,max_col_dict,min_col_dict,ce = lhs_by_feature(agg_feature,lhs_list,max_col_dict,min_col_dict,ce)
            # candidate rhs
            # c_k : candidate k
            for c_k in range(len(col_list)):
                if c_k < i or c_k > j:
                    # print(c_k)
                    candidate_col = col_list[c_k]
                    candidate_rhs = data[candidate_col][n]
                    if check_equal(lhs,candidate_rhs,ce) == False:
                        # violation_row[c_k].append(n)
                        violation_row[c_k].append([lhs_list,candidate_rhs])
                        violation_row_number[c_k].append(n)
        else:
            isexist = 0
            for _ in range(i,j):
                nanskip_pool.append(_)
            break
        
        
        _minlenlist_key = minlenlist_key(violation_row_number)
        if len(violation_row_number[_minlenlist_key]) > allow_rate*len(data):
            isexist = 0
            break
        # print(len(violation_row_number[_minlenlist_key]),round(len(violation_row_number[_minlenlist_key])/len(data),4))
        
    if agg_feature == 'max' and max(max_col_dict.values()) == n:
        isexist = 0
    elif agg_feature == 'min' and max(min_col_dict.values()) == n:
        isexist = 0
        
        
    return(isexist,violation_row_number,violation_row,nanskip_pool)


def minlenlist_key(_dict):
    minlen_list = min(_dict.values(), key=lambda x: len(x))
    for k in _dict.keys():
        if _dict[k] == minlen_list:
            return(k)

# not stop after discover
# agg_feature,data,col_list,allow_rate,ce = agg_feature,data,numerical_columns,max_violation_rate,rel_ce
def program_relationship_discover(agg_feature,data,col_list,allow_rate,ce):
    if len(col_list) <= 3:
        return []
    
    program_relationships = []
    for i in range(len(col_list)-1):
        start_col = col_list[i]
        for j in range(i+1,len(col_list)):
            formula_len = j-i+1
            if formula_len >= len(col_list) or formula_len < 3:
                continue
            end_col = col_list[j]
            violation_row,violation_row_number = init_vcol_dict(col_list,i,j)
            nanskip_pool = []
            isexist,violation_row_number,violation_row,nanskip_pool = find_rhs(agg_feature,data,col_list,violation_row,i,j,
                                                                               violation_row_number,nanskip_pool,allow_rate,ce)
            if isexist == 1:
                # k = min(violation_row_number, key=violation_row_number.get)
                k = minlenlist_key(violation_row_number)
                agg_col = col_list[k]
                program_relationships.append([isexist, start_col, end_col, agg_col, violation_row_number[k]])
                # return(isexist, start_col, end_col, agg_col, violation_row[k])
            elif  len(nanskip_pool) != 0:
                break
        if i in nanskip_pool:
            continue
    return(program_relationships)

def consecutive_numeric_columns(data,position=[]):
    if position == []:
        columns = data.columns.values.tolist()
        lhs_cols = []
        agg_col_list = []
        for column in columns:
            if data[column].dtype in ['int32','int64','float64']:
                lhs_cols.append(column)
            elif lhs_cols != []:
                lhs_cols = []
    else:
        start_col,end_col,agg_col = position
        columns = data.columns.values.tolist()
        lhs_cols = []
        for _column in position:
            if data[_column].dtype not in ['int32','int64','float64']:
                return([],[])
            
        for column in columns:
            if columns.index(column) < columns.index(start_col):
                continue
            elif columns.index(column) > columns.index(end_col):
                break
            
            if data[column].dtype in ['int32','int64','float64']:
                lhs_cols.append(column)
            else:
                return([],[])
        agg_col_list = lhs_cols + [agg_col]
    
    if lhs_cols != []:
        return(agg_col_list,lhs_cols)
    else:
        return([],[])  

def gen_instance(data,cols,skip_rows=[]):
    instance = []
    if len(data)-len(skip_rows) > 5:
        for i in range(len(data)):
            if i in skip_rows:
                continue
            if len(instance)>=5:
                break
            ins = []
            for j in range(len(cols)):
                ins.append(data[cols[j]][i])
            instance.append(tuple(ins))
    else:
        for i in range(len(data)):
            if i in skip_rows:
                continue
            ins = []
            for j in range(len(cols)):
                ins.append(data[cols[j]][i])
            instance.append(tuple(ins))
    return(instance)

def hypothesis_testing1(Dict,Dict_num,m,col_number):
    probs = []
    for i in range(col_number):
        numerator = 0
        denominator = m
        # Dict[i] stands for column i's dictionary
        for key in Dict[i].keys():
            count = 0
            count = 1-sum(Dict_num[i][key])/m
            numerator += count*sum(Dict_num[i][key])
            # print(key,numerator/denominator)
        score = numerator/denominator
        probs.append(score)
    prob = min(probs)
    return(prob)



def gen_dict(data,agg_col_list,skip_rows=[]):
    # for n in range(len(agg_col_list)):
    ################Generate dict
    # example
    # agg_col_list: a  b  c  d
    # elements:     10 20 30 40
    # [{} {} {} {}]
    # when i = 0, k[i] = 10 
    # {10:[(20,30,40),(12,13,14)]}
    # {10:[1,2]}
    Dict = [{} for _ in range(len(agg_col_list))]
    Dict_num = [{} for _ in range(len(agg_col_list))]
    for _ in range(len(data)):
        if _ in skip_rows:
            continue
        # elements = [data[agg_col_list[n][i]][_] for i in range(len(agg_col_list))]
        elements = [data[agg_col_list[i]][_] for i in range(len(agg_col_list))]
        allnum_token,elements = allnum(elements)
        if allnum_token == 1:
            k = elements
            v = []
            for i in range(len(agg_col_list)):
                v.append(tuple(elements[:i] + elements[i+1:]))
            # for i in range(len(agg_col_list)):
                if k[i] not in Dict[i].keys():
                    Dict[i][k[i]],Dict_num[i][k[i]] = [],[]
                if v[i] not in Dict[i][k[i]]:
                    Dict[i][k[i]].append(v[i]) 
                    Dict_num[i][k[i]].append(1)
                else:
                    Dict_num[i][k[i]][Dict[i][k[i]].index(v[i])] += 1
    return(Dict,Dict_num)


def HT_sample_test(data,col_start,col_end,col_sum,skip_rows):
    ###################
    start_col,end_col,agg_col = col_start,col_end,col_sum
    agg_col_list,lhs_cols = consecutive_numeric_columns(data,position=[start_col,end_col,agg_col])
    
    # Dict,Dict_num = gen_dict(data,agg_col_list,skip_rows)
    Dict,Dict_num = gen_dict(data,agg_col_list,skip_rows)
    if Dict == [{} for _ in range(len(agg_col_list))]:
        ht1 = -1
    else:
        ht1 = hypothesis_testing1(Dict,Dict_num,len(data)-len(skip_rows),len(agg_col_list))
    # instance = gen_instance(data,agg_col_list,skip_rows)
    # return(ht1,instance)
    return ht1


def sum_discovery_and_ht_test(use_ht2,data,numerical_columns,ht1_threshold,ht2_threshold,max_violation_rate,rel_ce):
    sum_dict = {}
    agg_feature = 'sum'
    sum_list = program_relationship_discover(agg_feature,data,numerical_columns,max_violation_rate,rel_ce)
    for i in range(len(sum_list)):
        isexist,col_start,col_end,col_sum,skip_rows  = sum_list[i]

        if use_ht2 == True:
            data_columns = list(data.columns)
            col_start_index = data_columns.index(col_start)
            col_end_index = data_columns.index(col_end_index)
            formula_cols = data_columns[col_start_index:col_end_index+1] + [col_sum]
            ht2_filter, ht2_score = hypothesis_testing2.get_ht2_score(data,data_columns,formula_cols,skip_rows,ht2_threshold)

            if ht2_filter == True:
                continue
        # ht1,instance = HT_sample_test(data,col_start,col_end,col_sum,skip_rows)
        ht1 = HT_sample_test(data,col_start,col_end,col_sum,skip_rows)
        ht1 = 1-ht1
        # print(ht1)
        # if ht1 < 1:
        #     print(ht1,col_start,col_end,col_sum)
        
        if ht1 <= ht1_threshold:
            sum_dict[(col_start,col_end,col_sum)] = ht1
                
    return sum_dict

# data = data_transposed
def program_discovery_and_ht_test(agg_feature,data,numerical_columns,use_ht2,
                                  ht1_threshold,ht2_threshold,max_violation_rate,rel_ce):
    program_dict = {}
    # agg_feature = 'sum'
    # program_list = [[1, 'Column1', 'Column3', 'Column4', []]]
    program_list = program_relationship_discover(agg_feature,data,numerical_columns,max_violation_rate,rel_ce)
    # program_list = program_relationship_discover(agg_feature,data,numerical_columns,max_violation_rate,0.01)
    for i in range(len(program_list)):
        isexist,col_start,col_end,col_agg,skip_rows  = program_list[i]

        if use_ht2 == True:
            data_columns = list(data.columns)
            col_start_index = data_columns.index(col_start)
            col_end_index = data_columns.index(col_end)
            formula_cols = data_columns[col_start_index:col_end_index+1] + [col_agg]
            ht2_filter, ht2_score = hypothesis_testing2.get_ht2_score(data,data_columns,formula_cols,skip_rows,ht2_threshold)

            if ht2_filter == True:
                continue
        # ht1,instance = HT_sample_test(data,col_start,col_end,col_agg,skip_rows)
        ht1 = HT_sample_test(data,col_start,col_end,col_agg,skip_rows)
        ht1 = 1-ht1
        # print(ht1)
        # if ht1 < 1:
        #     print(ht1,col_start,col_end,col_agg)
        
        if ht1 <= ht1_threshold:
            program_dict[(col_start,col_end,col_agg)] = ht1
                
    return program_dict
