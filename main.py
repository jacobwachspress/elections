# -*- coding: utf-8 -*-
"""
Created on Fri Jul 24 13:08:40 2020

@author: Jacob
"""

import pandas as pd
import numpy as np
from datetime import date
from voter_power import state_voter_powers

# set update date and election date
last_update = date(2020, 7, 18)
election_day = date(2020, 11, 3)
days_to_election = (election_day - last_update).days

# initialize moneyball path
money_path = 'G:/Shared drives/princeton_gerrymandering_project/Moneyball/'
path = money_path + 'state/'

# read in input DataFrame
races_df = pd.read_csv('data/output/CNalysis/all_input_data.csv')

# read in and merge foundations margin
found_direc = 'data/output/foundation/'
founds_df = pd.read_csv(found_direc + 'foundations_predictions_2020.csv')
founds_df['office'] = founds_df['chamber']
founds_df = founds_df[['state', 'district_num', 'office', 'found_margin']]
races_df = pd.merge(races_df, founds_df, how='left', on=['state', \
                                            'office', 'district_num'])

# read in states to test
to_test = pd.read_csv('data/input/parameters/states_and_thresholds.csv')

# merge to get thresholds
races_df = pd.merge(races_df, to_test, how='left', on=['state', 'office'])

# restrict to chambers where there is a threshold in the csv
races_df = races_df[races_df['d_threshold'].notna()]

# add column for statewide error
races_df['statewide'] = 1

# how much should we fatten the tails based on the time to election
deg_f_scale = 1 + min(1, 1/4*np.log(1 + days_to_election/20))

# set the correlated error vars
error_vars = {}
err_df = pd.read_csv('data/input/parameters/correlated_error_parameters.csv')
for _, row in err_df.iterrows():
    sigma = row['sigma']
    deg_f = row['deg_f']
    if row['decay'] == True:
        deg_f /= deg_f_scale
    error_vars[row['parameter']] = ((sigma, deg_f), row['nodes'])

# set the isolated race error    
race_sigma = 0.07
race_deg_f = 5 / deg_f_scale
# set DataFrame columns for voter power analysis
margin_col = 'margin' 
voters_col = 'cvap'
threshold_col = 'd_threshold'
tie_col = 'tie_dem'
chamber_col = 'office'
power_col = 'VOTER_POWER'

# initialize list of bipartisan control probabilities 
bipart_probs = []

# for each state
for state in ['NC']:
    
    # find probablity of bipartisan control of residistricting
    
    # no blending for NC, all Chaz (redistricting since 2018 messes up founds)
    if state != 'NC':
        bipart_prob = state_voter_powers(races_df, state, error_vars, race_sigma, 
                            race_deg_f, margin_col, voters_col,
                            threshold_col, tie_col, chamber_col, power_col,
                            found_margin_col='found_margin', found_clip=0.06, 
                            blend_safe=0.75, blend_else=0.5, just_get_prob=True)
    
    else:
        bipart_prob = state_voter_powers(races_df, state, error_vars, race_sigma, 
                            race_deg_f, margin_col, voters_col,
                            threshold_col, tie_col, chamber_col, power_col,
                            just_get_prob=True)
    
    
    bipart_probs.append(bipart_prob)
    print(bipart_prob)
    
# # write results to DataFrame
# bipartisan_control_df = pd.DataFrame({'state' : ['CT'], \
#                                       'bipartisan_prob': bipart_probs})
# bipartisan_control_df.to_csv(money_path + 'output/bipartisan_control_CT.csv')

print ('win probs done')
    

results = []

# for each state
for state in ['CT']:
    print ('starting ' + state)
    try:
    
        # no blending for NC, all Chaz (redistricting since 2018 messes up founds)
        if state == 'NC':
            power_df = state_voter_powers(races_df, state, error_vars, race_sigma, 
                            race_deg_f, margin_col, voters_col,
                            threshold_col, tie_col, chamber_col, power_col)
        
        else:    
            # find probablity of pvoter powers for districts in this state
            power_df = state_voter_powers(races_df, state, error_vars, race_sigma, 
                                    race_deg_f, margin_col, voters_col,
                                    threshold_col, tie_col, chamber_col, power_col,
                                    found_margin_col='found_margin', 
                                    found_clip=0.06, blend_safe=0.75, blend_else=0.5)
        
        # append to results dataframe
        results.append(power_df)
        power_df.to_csv(money_path + 'output/' + state + '_7_28.csv')
    except:
        print('failed')
    
# concatenate statewide dataframes
output_df = pd.concat(results) 

# output_df.to_csv(money_path + 'output/' + 'all_results_raw.csv')

# delete unecessary columns
output_df = output_df[['state', 'district', 'incumbent', 'favored', 
                      'confidence', 'nom_R', 'nom_D', 'nom_I', 
                      'cvap', 'VOTER_POWER']]

# output_df.to_csv(money_path + 'output/' + 'all_results.csv')