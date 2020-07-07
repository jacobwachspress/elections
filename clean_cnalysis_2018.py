# -*- coding: utf-8 -*-
"""
Created on Fri Jul  3 11:24:17 2020

@author: Jacob
"""

import pandas as pd
import numpy as np
import operator
import os
import difflib

# CLEAN 2018 ELECTION DATA #

# set google drive path for files
moneyball_path = 'G:\\Shared drives\\princeton_gerrymandering_project\\Moneyball\\'

# read in 2018 results from MEDSL
df = pd.read_csv(moneyball_path + "testing\\state_overall_2018.csv")

# Filter to state assembly/senate offices
partial_term = 'State Representative (Partial Term Ending 01/01/2019)'
relevant_offices = ['House of Delegates Member', 'State Assembly Member',
                    'State Assembly Representative',
                    'State House Delegate', 'State Representative',
                    partial_term, 'State Representative A',
                    'State Representative B',
                    'State Representative Pos. 1',
                    'State Representative Pos. 2', 'State Senate',
                    'State Senator',
                    'State Senator Partial Term Ending (01/01/2019)']
senate_offices = ['State Senate', 'State Senator',
                  'State Senator Partial Term Ending (01/01/2019)']
df = df[df['office'].isin(relevant_offices)]

# Identify which chamber each race is
df['office'] = df['office'].apply(lambda x: 'upper' if x in senate_offices
                                   else 'lower')

# get total votes per candidate, filter out unimportant columns
cols_to_group = ['year', 'state_po', 'office', 'district', 'candidate']
df_grouped = df.groupby(cols_to_group).agg({'candidatevotes' : sum, \
                    'party' : 'first'}).reset_index()

# remove non-votes
non_candidates = ['Blank', 'Blank Votes', 'NA NA', 'NA Davis', 'Over Votes', \
                  'Under Votes', 'Void']
df_grouped = df_grouped[~df_grouped['candidate'].isin(non_candidates)]

# clean parties
df['party'] = df['party'].apply(lambda x: x if x in ['democrat', \
                  'republican', 'independent'] else 'other_party')



# get indices of winning candidates
cols_to_group = ['year', 'state_po', 'office', 'district']
winner_ixs = df_grouped.groupby(cols_to_group)['candidatevotes'].idxmax().values
df_grouped['Winner'] = False
df_grouped.loc[winner_ixs, 'Winner'] = True
df = df_grouped.reset_index()

# get total votes in each race
df_grouped = df.groupby(cols_to_group)['candidatevotes'].sum().reset_index()
df_grouped['totalvotes'] = df_grouped['candidatevotes']
df_grouped = df_grouped.drop(['candidatevotes'], axis=1)
df = pd.merge(df, df_grouped, how='left', on=cols_to_group)

# get vote percents
df['vote_pct'] = df.apply(lambda x: x['candidatevotes'] / x['totalvotes'], \
                      axis=1)


# for every (year, state_po, office, district)
years = list(set(df['year']))
for year in years:
    year_df = df[df['year'] == year]
    state_pos = list(set(year_df['state_po']))
    for state_po in state_pos:
        state_po_df = year_df[year_df['state_po'] == state_po]
        offices = list(set(state_po_df['office']))
        for office in offices:
            office_df = state_po_df[state_po_df['office'] == office]
            districts = list(set(office_df['district']))
            for district in districts:
                district_df = office_df[office_df['district'] == district]
                
                # get a dictionary of party : vote_pct in the election
                d = dict(zip(district_df['party'], district_df['vote_pct']))
                
                # find winning party
                win_party = max(d.items(), key=operator.itemgetter(1))[0]
                
                # find winning margin
                voteshares = sorted(list(d.values()))
                if len(voteshares) == 1:
                    win_margin = 1
                else:
                    win_margin = voteshares[-1] - voteshares[-2]
                for i, _ in district_df.iterrows():
                    df.loc[i, 'win_party'] = win_party
                    df.loc[i, 'win_margin'] = win_margin
                    
                

## FUZZY MERGE CHAZ AND ELECTION RESULTS ##
def fuzzy_merge(file, df):

    # get state and chamber from file name of the form 'ST_chamber.csv'
    state = file.split('_')[0]
    chamber = file.split('_')[1][:-4]
    
    # get chaz df for state and chamber
    chaz_df = pd.read_csv(moneyball_path + 'chaz\\cleaned_states\\' + \
                          state + '_' + chamber + '.csv', dtype=str).dropna()

    # deal with chaz inconsistency in chaz rating column label
    rating_col = chaz_df.columns[-1]
    
    # get rating and confidence
    chaz_df['predicted_winner'] = chaz_df.apply(lambda x: \
                                       x[rating_col].split(' ')[1], axis=1)
    chaz_df['confidence'] = chaz_df.apply(lambda x: \
                                       x[rating_col].split(' ')[0], axis=1)
    
    # drop uncontested / no election (no results for many uncontested)
    chaz_df = chaz_df[~chaz_df['confidence'].isin(['No', 'Uncontested'])]
        
    # get election results in this chamber
    results_df = df[df['state_po'] == state]
    results_df = results_df[results_df['office'] == chamber]
    
    # filter for winners
    results_df = results_df[results_df['Winner'] == 'True']
    
    # clean district names (get rid of "District" at the front)
    results_df['district'] = results_df['district'].apply(lambda x: \
             ' '.join(x.split(' ')[1:]) if x.split(' ')[0] == 'District' \
                     else x)
    
    # fuzzy guess the name of the district
    chaz_df['DIST_NAME'] = chaz_df['NAME'].apply(lambda x: \
           difflib.get_close_matches(x, results_df['district'])[0] \
           if len(difflib.get_close_matches(x, results_df['district'])) > 0\
                  else None)
    
    # merge dataframes
    new_chaz_df = pd.merge(chaz_df, results_df, how='left', \
                               left_on='DIST_NAME', right_on='district')
    
    # set index to new name and return
    return new_chaz_df.set_index('DIST_NAME')

dfs = [fuzzy_merge(file, df) for file in \
           os.listdir(moneyball_path + 'chaz\\cleaned_states\\')]

merged_df = pd.concat(dfs)
cols_to_keep = ['NAME', 'state_po', 'office', 'GEOID', 'confidence', \
                'predicted_winner', 'win_party', 'win_margin']
merged_df = merged_df[cols_to_keep]

# WISCONSIN, MANUAL CHANGES
    
        
    
    

