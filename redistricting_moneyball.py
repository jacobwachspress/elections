# -*- coding: utf-8 -*-
"""
Created on Fri Jul 24 13:08:40 2020

@author: Jacob
"""

import pandas as pd
import numpy as np
from datetime import date
from voter_power import state_voter_powers
import scipy.stats as sts


# set update date and election date
last_update = date(2020, 10, 10)
election_day = date(2020, 11, 3)
days_to_election = (election_day - last_update).days

# get current month, day, year for file saving
today = date.today()
datestring = '_' + str(today.month) + '_' + str(today.day) + '_' + \
                        str(today.year)

# read in input DataFrame
races_df = pd.read_csv('data/output/CNalysis/all_input_data.csv')

# read in and merge foundations margin
pred_path = 'data/output/foundation/foundations_predictions_2020.csv'
founds_df = pd.read_csv(pred_path)
founds_df['office'] = founds_df['chamber']
founds_df = founds_df[['state', 'district_num', 'office', 'found_margin']]
races_df = pd.merge(races_df, founds_df, how='left',
                    on=['state', 'office', 'district_num'])

# nebraska unicameral hack
races_df.loc[(races_df['state'] == 'DE') &
             (races_df['office'] == 'lower'), 'state'] = 'NE'
             
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
    if row['decay']:
        deg_f /= deg_f_scale
    error_vars[row['parameter']] = ((sigma, deg_f), row['nodes'])

# set the isolated race error
race_sigma = 0.07
race_deg_f = 5 / deg_f_scale

# get t-distribution cdf (bottleneck if not pre-calculated)
tcdf = sts.t.cdf(np.linspace(-50, 50, 10000000), race_deg_f)

# set DataFrame columns for voter power analysis
margin_col = 'margin'
voters_col = 'turnout_estimate'
threshold_col = 'd_threshold'
tie_col = 'tie_dem'
chamber_col = 'office'
power_col = 'VOTER_POWER'

# read csv into ratings_to_margin DataFrame
path = 'data/input/parameters/CNalysis_rating_to_margin.csv'
rating_to_margin_df = pd.read_csv(path, index_col='RATING')

# initialize list of bipartisan control probabilities
bipart_probs = []

# for each state
for state in races_df['state'].unique():
    print(state)

    # find probablity of bipartisan control of residistricting

    # no blending for NC, all Chaz (redistricting since 2018 messes up founds)
    if state in ['NE', 'NC']:
        bipart_prob = state_voter_powers(races_df, margin_col, voters_col,
                                         threshold_col, tie_col, chamber_col,
                                         power_col, state, error_vars,
                                         race_sigma, race_deg_f,
                                         rating_to_margin_df, tcdf,
                                         prob_only=True)
    else:
        bipart_prob = state_voter_powers(races_df, margin_col, voters_col,
                                         threshold_col, tie_col, chamber_col,
                                         power_col, state, error_vars,
                                         race_sigma, race_deg_f,
                                         rating_to_margin_df, tcdf,
                                         found_margin_col='found_margin',
                                         found_clip=0.06,
                                         blend_safe=0.75, blend_else=0.5,
                                         prob_only=True)

    bipart_probs.append(bipart_prob)

# write results to DataFrame
bipartisan_control_df = pd.DataFrame({'state': races_df['state'].unique(),
                                      'bipartisan_prob': bipart_probs})

# write these DataFrame to a csv
bipartisan_control_df.to_csv('data/output/voter_power/bipartisan_prob' +
                             datestring + '.csv', index=False)
print('win probs done')

results = []

# for each state
for state in races_df['state'].unique():
    print('starting ' + state)

    # no blending for NC, all CNalysis (maps redrawn in 2018)
    if state in ['NE', 'NC']:
        power_df = state_voter_powers(races_df, margin_col, voters_col,
                                      threshold_col, tie_col, chamber_col,
                                      power_col, state, error_vars,
                                      race_sigma, race_deg_f,
                                      rating_to_margin_df, tcdf)
    else:
        power_df = state_voter_powers(races_df, margin_col, voters_col,
                                      threshold_col, tie_col, chamber_col,
                                      power_col, state, error_vars,
                                      race_sigma, race_deg_f,
                                      rating_to_margin_df, tcdf,
                                      found_margin_col='found_margin',
                                      found_clip=0.06,
                                      blend_safe=0.75, blend_else=0.5)

    # append to results dataframe
    results.append(power_df)
    power_df.to_csv('data/output/voter_power/' + state +
                    datestring + '.csv', index=False)


# concatenate statewide dataframes
output_df = pd.concat(results)

# adjust for number of seats at stake
seats_df = pd.read_csv('data/input/parameters/cong_dist_proj_2021.csv')
seats_dict = dict(zip(seats_df['state'], seats_df['cong_proj']))
redist_col = 'redistricting_voter_power'
output_df[redist_col] = output_df.apply(lambda x: x['VOTER_POWER'] *
                                        (seats_dict[x['state']] - 1),
                                        axis=1)

# save raw output file
output_df.to_csv('data/output/voter_power/all_results_raw' +
                 datestring + '.csv', index=False)

# delete unecessary columns
output_df = output_df[['state', 'district', 'incumbent', 'favored',
                       'confidence', 'nom_R', 'nom_D', 'nom_I', 'cvap',
                       'VOTER_POWER', 'redistricting_voter_power']]

output_df.to_csv('data/output/voter_power/all_results' +
                 datestring + '.csv', index=False)
