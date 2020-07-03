# -*- coding: utf-8 -*-
"""
Created on Fri Jul  3 11:24:17 2020

@author: Jacob
"""

import pandas as pd
import numpy as np
import operator

# CLEAN 2018 ELECTION DATA #

# set google drive path for files
moneyball_path = 'G:\\Shared drives\\princeton_gerrymandering_project\\Moneyball\\'

# read in 2018 results from MEDSL
df = pd.read_csv(moneyball_path + "testing\\state_overall_2018.csv")

# restrict to offices of interest
df = df[df['office'].isin(['State Senate',
 'State Senator', 'state Representative'])]

# Remove state_pos with multi-member districts
df = df[~df['state_po'].isin(['Vermont', 'West Virginia', 'Washington', \
        'Idaho'])]

# clean office titles
df['office'] = df['office'].apply(lambda x: 'senate' if x in ['State Senate', \
                  'State Senator'] else 'house')

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
                    
                


