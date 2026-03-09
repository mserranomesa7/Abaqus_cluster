# -*- coding: utf-8 -*-
import sys
sys.path.append('.')   # ensures current dir is in path for utils.py
from functions_param_for_CAE import (insert_amplitude_block_after_end_assembly, add_bond_block, add_boundary_conditions_block_full,add_interaction_block_full,add_steps_block_full)

export_modified_inp = True
file_param = "251117-concrete_param" # "251117-concrete_param" # "251311-tendon_distance"
path = f'../CAE/base_models/{file_param}'
sp = 'c2.5'
file_name = f'250923-CAE_Python_c2.5_full_base_model_fcm70_Ecm20'
file_name_prefix= "251203-CAE_Python_c2.5_full_fcm70_Ecm20"
inp_CAE_outfile = f'{path}/{file_name}.inp'

# Parameters
param_study = False
friction_value = 1.3 # friction coefficient for bond [-]
friction_list = [1.1, 1.2, 1.3] # friction values for param study
fcm_list = [80, 90, 100, 110, 120]
# ept_list = [8800, 12000, 15000]

F_p = 132515 # 132515 # 79600 # prestress force [N]

if param_study:
    for fcm in fcm_list:
        # Modify the inp file
        # 1. Read the input .inp file into a string
        inp_CAE_outfile = f'{path}/{file_name_prefix}_base_model_fcm{fcm}.inp'
        inp_modified_outfile = f'{path}/../../modified_INP/{file_param}/{file_name_prefix}_fcm{fcm}_inp_modified.inp'

        with open(inp_CAE_outfile, 'r') as f:
            modified_inp = f.read()

        # 2. Add blocks
        modified_inp = insert_amplitude_block_after_end_assembly(modified_inp)
        modified_inp = add_bond_block(modified_inp, friction_value=friction_value)  # bond
        modified_inp = add_boundary_conditions_block_full(modified_inp)             # NEW BCs (two strands, no Surf_side)
        modified_inp = add_interaction_block_full(modified_inp)                          # interaction
        modified_inp = add_steps_block_full(modified_inp, F_p)

        # 3. Write the result
        with open(inp_modified_outfile, 'w') as f:
            f.write(modified_inp)
        print("✅ Final .inp file saved as {}".format(inp_modified_outfile))

else:
    inp_modified_outfile = f'{path}/../../modified_INP/{file_param}/{file_name_prefix}_inp_modified.inp'
    # Modify the inp file
    # 1. Read the input .inp file into a string
    with open(inp_CAE_outfile, 'r') as f:
        modified_inp = f.read()

    # 2. Add blocks
    modified_inp = insert_amplitude_block_after_end_assembly(modified_inp)
    modified_inp = add_bond_block(modified_inp, friction_value=friction_value)  # bond
    modified_inp = add_boundary_conditions_block_full(modified_inp)  # NEW BCs (two strands, no Surf_side)
    modified_inp = add_interaction_block_full(modified_inp)  # interaction
    modified_inp = add_steps_block_full(modified_inp, F_p)

    # 3. Write the result
    with open(inp_modified_outfile, 'w') as f:
        f.write(modified_inp)
    print("✅ Final .inp file saved as {}".format(inp_modified_outfile))