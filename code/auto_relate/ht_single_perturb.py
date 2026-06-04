import numpy as np


def run(Dict,Dict_num,m,col_number,ops):
    if col_number == 2 or col_number == 3:
        prob = col_score_allcols(Dict,Dict_num,m,col_number)
    else:
        if '*' not in ops:
            artype = 0
            prob = col_score_allcols(Dict,Dict_num,m,col_number)
        elif ops[0] == '*' and ops[1] == '*':
            artype = 3
            probs = []
            # col 1, 2, 3
            for i in range(0,3):
                # print(i)
                j = 0
                Dict_update,Dict_num_update,loss_num_1 = update_dict(Dict,Dict_num,i,j)
                j = 1
                Dict_update,Dict_num_update,loss_num_2 = update_dict(Dict_update,Dict_num_update,i,j)
                loss_num = loss_num_1 + loss_num_2
                score = col_score(Dict_num_update,i,m,loss_num)
                probs.append(score)
            # col 4
            i = 3
            score = col_score(Dict_num,i,m)
            probs.append(score)
                
            prob = sum(probs)/col_number
        # (a op1 b) op2 c
        # a b parameters: a vs b
        elif ops[0] == '*':
            artype = 1
            probs = []
            # col 1 :
            i = 0
            j = 0
            Dict_update,Dict_num_update,loss_num = update_dict(Dict,Dict_num,i,j)
            score = col_score(Dict_num_update,i,m,loss_num)
            probs.append(score)
            # col 2
            i = 1
            j = 0
            Dict_update,Dict_num_update,loss_num = update_dict(Dict,Dict_num,i,j)
            score = col_score(Dict_num_update,i,m,loss_num)
            probs.append(score)
            
            # col 3 4
            for i in range(2,4):
                # print(i)
                score = col_score(Dict_num,i,m)
                probs.append(score)
                
            prob = sum(probs)/col_number
            # print(probs)
        # c parameter
        elif ops[1] == '*':
            artype = 2
            probs = []
            # col 1, 2
            for i in range(0,2):
                # print(i)
                j = 1
                Dict_update,Dict_num_update,loss_num = update_dict(Dict,Dict_num,i,j)
                score = col_score(Dict_num_update,i,m,loss_num)
                probs.append(score)
            for i in range(2,4):
                # print(i)
                score = col_score(Dict_num,i,m)
                probs.append(score)
                
            prob = sum(probs)/col_number
            
    return(1-prob)


##################

def col_score_allcols(Dict,Dict_num,m,col_number):
    probs = []
    for i in range(col_number):
        numerator = 0
        denominator = m
        # Dict[i] stands for column i's dictionary
        for key in Dict[i].keys():
            count = 0
            # count = 1-(sum(Dict_num[i][key])-1)/(m-1)
            count = 1-sum(Dict_num[i][key])/m
            numerator += count*sum(Dict_num[i][key])
        score = numerator/denominator
        # score = col_score(Dict_num,i,m)
        probs.append(score)
    prob = sum(probs)/col_number
    return(prob)



def update_dict(Dict,Dict_num,current_col,zero_col):
    loss_num = 0
    Dict_update_col = {}
    Dict_num_update_col = {}
    for key in Dict[current_col].keys():
        Dict_update_col[key] = []
        Dict_num_update_col[key] = []
        # for triad in Dict[current_col][key]:
        for i in range(len(Dict[current_col][key])):
            triad = Dict[current_col][key][i]
            triad_num = Dict_num[current_col][key][i]
            if triad[zero_col] != 0:
                Dict_update_col[key].append(triad)
                Dict_num_update_col[key].append(triad_num)
            else:
                loss_num += triad_num 
        if Dict_update_col[key] == []:
            del Dict_update_col[key]
            del Dict_num_update_col[key]
            
    Dict_update = []
    Dict_num_update = []
    for i in range(len(Dict)):
        if i == current_col:
            Dict_update.append(Dict_update_col)
            Dict_num_update.append(Dict_num_update_col)
        else:
            Dict_update.append(Dict[i])
            Dict_num_update.append(Dict_num[i])
    
    return(Dict_update,Dict_num_update,loss_num)

# the main difference betweem two version is the dict used.
def col_score(Dict_num,sub_dict_id,m,loss_num=0):
    numerator = 0
    denominator = m
    sub_dict = Dict_num[sub_dict_id]
    for key in sub_dict.keys():
        count = 0
        # count = (m-loss_num-sum(Dict_num[sub_dict][key]))/m
        count = (m-loss_num-sum(sub_dict[key]))/m
        # count = (m-loss_num-sum(sub_dict[key]))/(m-1)
        numerator += count*sum(sub_dict[key])
        # print(key,numerator/denominator)
    score = numerator/denominator
    return score



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


def allnum(elements):
    token = 1
    new_elements = []
    for elem in elements:
        # To prevent overflow of int64 variables, numbers greater than 
        # the square root of the maximum value of int64 have been excluded.
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
