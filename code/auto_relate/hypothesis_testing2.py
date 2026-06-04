import pandas as pd
from  scipy.stats import chi2_contingency


# no save version
# def filter_by_P_value(data,num_cols,for_cols,violation_rows,p_threshold):
def filter_by_P_value(data,total_cols,formula_cols,violation_rows,p_threshold):
    # in numerical data, num_cols,for_cols = total_cols,formula_cols
    if len(violation_rows) == 0:
        return False
        # return('','')
    
    formula_test = []
    for n in range(len(data)):
        if n in violation_rows:
            formula_test.append(0)
        else:
            formula_test.append(1)
    data['formula_test'] = formula_test
    
    com_cols = list(set(total_cols).difference(set(formula_cols)))
    
    for col in com_cols:
        crosstab = pd.crosstab(data['formula_test'],data[col])
        cs_score = chi2_contingency(crosstab)[1]
        if cs_score < p_threshold:
            return True
    return False
    # return('',cs_score)

def get_ht2_score(data,total_cols,formula_cols,violation_rows,p_threshold):
# in numerical data, num_cols,for_cols = total_cols,formula_cols
    if len(violation_rows) == 0:
        # return False
        return('', '')
    
    formula_test = []
    for n in range(len(data)):
        if n in violation_rows:
            formula_test.append(0)
        else:
            formula_test.append(1)
    data['formula_test'] = formula_test
    
    com_cols = list(set(total_cols).difference(set(formula_cols)))
    
    for col in com_cols:
        crosstab = pd.crosstab(data['formula_test'],data[col])
        cs_score = chi2_contingency(crosstab)[1]
        if cs_score < p_threshold:
            # return True
            return(True, cs_score)
        
    # return False
    return(False, cs_score)