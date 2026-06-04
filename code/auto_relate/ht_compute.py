
import time
###################
import ht_single_perturb
import hypothesis_testing1
import class_create
import optimization_flags
import optimization_stats

def run(data,formula,option_selection,columns,ops,rel_ce,abs_ce,violation_rows):
    _is_null,Dict,Dict_num = is_null_dict(data,columns,violation_rows)
    if _is_null == True:
        print('_is_null == True, skip ',formula)
        return(1)
    HT_Result = class_create.HT_Score()
    HT_Result,per_running_time = calculated_score(data,Dict,Dict_num,columns,formula,rel_ce,abs_ce,
                                                  ops,violation_rows,HT_Result,option_selection)
    HT_score = HT_Result.ht_list[0]
    return(HT_score)


def is_null_dict(data,col_pair,skip_rows):
    Dict,Dict_num = ht_single_perturb.gen_dict(data,col_pair,skip_rows)
    if Dict == [{} for _ in range(len(col_pair))]:
        return(True,Dict,Dict_num)
    return(False,Dict,Dict_num)

def calculated_score(data,Dict,Dict_num,col_pair,formula,rel_ce,abs_ce,ops,skip_rows,HT_Result,option_selection):
    # HT_Result = class_create.HT_Score()
    
    start = time.perf_counter()
    if option_selection == 'single_perturb':
        optimization_stats.incr("ht_single_perturb_calls")
        # ht1 = HT.hypothesis_testing1_option1(Dict,Dict_num,len(data)-len(skip_rows),len(col_pair))
        if optimization_flags.disable_closed_form():
            optimization_stats.incr("closed_form_disabled_calls")
            ht1 = hypothesis_testing1.singlecol_sample(data, col_pair, formula, rel_ce, abs_ce, skip_rows)
        else:
            optimization_stats.incr("closed_form_used_calls")
            ht1 = ht_single_perturb.run(Dict,Dict_num,len(data)-len(skip_rows),len(col_pair),ops)
        HT_Result.ht_list = [ht1]
        # return(HT_Result,round(finish-start,2))
    elif option_selection == 'navie_sample':
        optimization_stats.incr("ht_naive_sample_calls")
        ht1_navie_sample = hypothesis_testing1.navie_sample(data,col_pair,2,formula,rel_ce,abs_ce,skip_rows)
        # ht1_navie_sample = hypothesis_testing1.navie_sample(data,col_pair,'random',formula,ce,skip_rows)
        HT_Result.ht_list = [ht1_navie_sample]
        # return(HT_Result,round(finish-start,2))
    elif option_selection == 'bound_sample':
        optimization_stats.incr("ht_bound_sample_calls")
        has_upper_bound = 0
        ht1_bound_sample,bound = hypothesis_testing1.bound_sample(has_upper_bound,data,col_pair,2,formula,rel_ce,abs_ce,skip_rows)
        # ht1_bound_sample = hypothesis_testing1.bound_only_once(data,col_pair,2,formula,ce,skip_rows)
        HT_Result.ht_list = [ht1_bound_sample]
        HT_Result.bound = bound
        # return(HT_Result,round(finish-start,2))
    elif option_selection == 'bound_sample_skip':
        optimization_stats.incr("ht_bound_sample_skip_calls")
        has_upper_bound = 1
        # ht1_bound_sample,bound = hypothesis_testing1.bound_sample(has_upper_bound,data,col_pair,'random',formula,ce,skip_rows,Dict=None,Dict_num=None,ops=None)
        ht1_bound_sample,bound = hypothesis_testing1.bound_sample(has_upper_bound,data,col_pair,'random',formula,
                                                                  rel_ce,abs_ce,skip_rows,Dict,Dict_num,ops)
        # print(ht1_bound_sample,bound)
        HT_Result.ht_list = [ht1_bound_sample]
        HT_Result.bound = bound
        
    finish = time.perf_counter()    
    return(HT_Result,round(finish-start,2))
