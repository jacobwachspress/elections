# -*- coding: utf-8 -*-
"""
Created on Tue Jul  7 15:29:39 2020

@author: Jacob
"""
import pandas as pd
import numpy as np
import scipy.stats as sts

# set google drive path for files
moneyball_path = 'G:\\Shared drives\\princeton_gerrymandering_project\\Moneyball\\'

# read in results
results = pd.read_csv(moneyball_path + \
                          'chaz\\chaz_prediction_results_2018.csv')

# filter oddball seats
results = results[results['ignore'] != True]

states = results['state_po'].dropna().unique()
confidences = results['confidence'].dropna().unique()

sts_df = pd.DataFrame({'STATE' : list(states) + ['USA']}).set_index('STATE')
for state, _ in sts_df.iterrows():
    
    # splice results DataFrame to get all results from this state
    if state != 'USA':
        state_df = results[results['state_po'] == state]
    else:
        state_df = results
        
    # for each confidence
    for conf in confidences:
        
        # splice df to only this confidence
        df = state_df[state_df['confidence'] == conf].copy()
        
        # find all outliers (probably surprise uncontesteds)
        outliers_df = df[df['win_margin'] > 0.9]
        sts_df.loc[state, conf + '_was_uncontested'] = len(outliers_df)
        
        # find all outlier misses
        outlier_losers_df = outliers_df[outliers_df['correct'] == False]
        sts_df.loc[state, conf + '_lost_uncontested'] = len(outlier_losers_df)
        
        # delete outliers
        df = df[df['win_margin'] <= 0.9]
        
        # find count of races in this category
        sts_df.loc[state, conf + '_count'] = len(df)
                                        
        # find mean winning margin
        sts_df.loc[state, conf + '_mean_win_margin'] = \
                                        df['actual_win_margin'].mean()
        
        # find stdev of winning margin
        sts_df.loc[state, conf + '_stdev_win_margin'] = \
                                df['actual_win_margin'].std()
        
        # if there are races
        if len(df) > 0:                 
            # fit t-distribution
            deg_f, mean, sigma = sts.t.fit(df['actual_win_margin'])
            
            # save these
            sts_df.loc[state, conf + '_t_mean'] = mean
            sts_df.loc[state, conf + '_t_sigma'] = sigma
            sts_df.loc[state, conf + '_t_deg_f'] = deg_f
        
        