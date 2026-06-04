
import pandas as pd
import numpy as np


def violation_rate(case_df,violation_rows,threshold):
    if len(violation_rows)/len(case_df)>threshold:
        return True
    else:
        return False
    

def numeric_type(case_df,left_col,right_col):
    if pd.api.types.is_numeric_dtype(case_df[left_col]) and pd.api.types.is_numeric_dtype(case_df[right_col]):
        return True
    else:
        return False
    
