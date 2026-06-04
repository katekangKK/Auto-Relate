from pathlib import Path

import process_one_table

if __name__ == "__main__":
    max_violation_rate = 0
    data_path = Path(__file__).resolve().parent.parent / "testdata" / "test_data_program.csv"
    degree_of_parallelism = 20
    
    # arithmetic_discovery = False or 3 or 4
    # Set 'arithmetic_discovery' = False when no arithmetic relationship needs to be searched.
    # Set 'arithmetic_discovery' = the maximum number of formula variables (3 or 4)
    # when arithmetic relationships need to be searched.
    
    arithmetic_discovery = 4
    
    
    # program_discovery = False or the program list
    # Set 'program_discovery' = False when no program relationship needs to be searched.
    # Set 'program_discovery' = the program list (['sum'], ['mean'], ['sum','mean'])
    # when program relationships need to be searched.
    
    program_discovery = ['sum','mean']
    
    
    # col_relationship / row_relationship = True or False
    col_relationship = True 
    row_relationship = True
    
    
    arithmetic_formulas, program_formulas = process_one_table.run(max_violation_rate,str(data_path),degree_of_parallelism,
                                                                  arithmetic_discovery,program_discovery,
                                                                  col_relationship,row_relationship)

    for res in arithmetic_formulas:
        res.Print()
        
    for res in program_formulas:
        res.Print()

##################### 

# Program:  sum
# HT1 Score:  0.33333333333333337
# Start Column:  row_0
# End Column:  row_9
# Program Column:  row_10


# Program:  mean
# HT1 Score:  0.33333333333333337
# Start Column:  row_0
# End Column:  row_9
# Program Column:  row_11
