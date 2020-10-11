# -*- coding: utf-8 -*-
"""
Created on Fri Jul  3 11:24:17 2020

@author: Jacob
"""

import pandas as pd
import operator
import os
import difflib
from cnalysis_input_components import merge_densities


def fuzzy_merge(file, df):
    """Fuzzy merge chaz and election results."""
    # get state and chamber from file name of the form 'ST_chamber.csv'
    state = file.split('_')[0]
    chamber = file.split('_')[1][:-4]

    # get chaz df for state and chamber
    chaz_df = pd.read_csv(money_path + 'chaz/cleaned_states/' +
                          state + '_' + chamber + '.csv', dtype=str).dropna()

    # deal with chaz inconsistency in chaz rating column label
    rating_col = chaz_df.columns[-1]

    # get rating and confidence
    chaz_df['predicted_winner'] = chaz_df.apply(lambda x:
                                                x[rating_col].split(' ')[1],
                                                axis=1)
    chaz_df['confidence'] = chaz_df.apply(lambda x:
                                          x[rating_col].split(' ')[0],
                                          axis=1)

    # drop uncontested / no election (no results for many uncontested)
    chaz_df = chaz_df[~chaz_df['confidence'].isin(['No', 'Uncontested'])]

    # get election results in this chamber
    results_df = df[df['state_po'] == state].copy()
    results_df = results_df[results_df['office'] == chamber]

    # filter for winners
    results_df = results_df[results_df['Winner'] == True]

    # clean district names (get rid of "District" at the front)
    results_df['district'] = results_df['district'].apply(lambda x:
             ' '.join(x.split(' ')[1:]) if x.split(' ')[0] == 'District'
                     else x)

    # fuzzy guess the name of the district
    chaz_df['DIST_NAME'] = chaz_df['NAME'].apply(lambda x:
           difflib.get_close_matches(x, results_df['district'])[0]
           if len(difflib.get_close_matches(x, results_df['district'])) > 0
                  else None)

    # merge dataframes
    new_chaz_df = pd.merge(chaz_df, results_df, how='left',
                           left_on='DIST_NAME', right_on='district')

    # keep certain columns
    cols_to_keep = ['DIST_NAME', 'NAME', 'GEOID', 'state_po', 'office',
                    'confidence', 'predicted_winner', 'win_party',
                    'win_margin']
    new_chaz_df = new_chaz_df[cols_to_keep]

    # set return
    return new_chaz_df


# CLEAN 2018 ELECTION DATA #

# read in 2018 results from MEDSL
df = pd.read_csv(money_path + "chaz/state_overall_2018.csv")

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

# sort DataFrame so that the first instance of the candidate's party is
# the party under which they received the most votes
df = df.sort_values(by=['year', 'state_po', 'office', 'district', 'candidate',
                        'candidatevotes'],
                    ascending=[True, True, True, True, True, False])
# get total votes per candidate, filter out unimportant columns
cols_to_group = ['year', 'state_po', 'office', 'district', 'candidate']
df_grouped = df.groupby(cols_to_group).agg({'candidatevotes': sum,
                                            'party': 'first'}).reset_index()

# remove non-votes
non_candidates = ['Blank', 'Blank Votes', 'NA NA', 'NA Davis', 'Over Votes',
                  'Under Votes', 'Void']
df_grouped = df_grouped[~df_grouped['candidate'].isin(non_candidates)]

# clean parties
df['party'] = df['party'].apply(lambda x: x if x in ['democrat', 'republican',
                                                     'independent']
                                else 'other_party')

# get indices of winning candidates
cols_to_group = ['year', 'state_po', 'office', 'district']
winner_ixs = df_grouped.groupby(cols_to_group)['candidatevotes']
winner_ixs = winner_ixs.idxmax().values
df_grouped['Winner'] = False
df_grouped.loc[winner_ixs, 'Winner'] = True
df = df_grouped.reset_index()

# get total votes in each race
df_grouped = df.groupby(cols_to_group)['candidatevotes'].sum().reset_index()
df_grouped['totalvotes'] = df_grouped['candidatevotes']
df_grouped = df_grouped.drop(['candidatevotes'], axis=1)
df = pd.merge(df, df_grouped, how='left', on=cols_to_group)

# get vote percents
df['vote_pct'] = df.apply(lambda x: x['candidatevotes'] / x['totalvotes'],
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


states_path = money_path + 'chaz/cleaned_states/'
dfs = [fuzzy_merge(file, df) for file in os.listdir(states_path)]

merged_df = pd.concat(dfs).reset_index(drop=True)

merged_df.to_csv(money_path + 'chaz/merged_results.csv', index=False)

# Incorporate manual changes from when the fuzzy merge was off
manual = pd.read_csv(money_path + 'chaz/manual_2018_results.csv', dtype=str)
merged_df = pd.concat([manual, merged_df])
merged_df['GEOID'] = merged_df['GEOID'].astype(str).str.zfill(5)
merged_df = merged_df.drop_duplicates(['GEOID', 'office'])
merged_df = merged_df.sort_values(['state_po', 'office'])
merged_df['win_margin'] = merged_df['win_margin'].astype(float)

# data fix, since CT republicans file as independents as well
merged_df.loc[(merged_df['state_po'] == 'CT') &
              (merged_df['win_party'] == 'independent'),
              'win_party'] = 'republican'

# SOME MORE CLEANING #
results = merged_df.dropna(subset=['state_po']).copy()

# nebraska has nonpartisan elections in results, can't assess
results = results[results['state_po'] != 'NE']

# get parties of winners
names = {'democrat': 'D', 'democratic-farmer-labor': 'D',
         'democratic-npl': 'D', 'republican': 'R', 'conservative': 'R'}
results['win_party'] = results['win_party'].apply(lambda x: names[x]
                                                  if x in names else 'I')

# add some useful columns
results['correct'] = results.apply(lambda x: x['predicted_winner'] ==
                                   x['win_party'], axis=1)

results['actual_win_margin'] = results.apply(lambda x: x['win_margin'] *
                                             (2 * x['correct'] - 1), axis=1)

# merge in whether chaz thinks he was correct #
chaz_correctness_folders = {'lower': 'State House', 'upper': 'State Senate'}

# generate full chaz df of correctness ratings
dfs = []

for chamber in chaz_correctness_folders:
    for file in os.listdir(money_path + 'chaz/Prediction Results/' +
                           chaz_correctness_folders[chamber]):
        # read .xlsx
        df = pd.read_excel(money_path + 'chaz/Prediction Results/' +
                           chaz_correctness_folders[chamber] + '/' + file,
                           dtype=str)

        # standardize correctness column
        df = df.rename(columns={df.columns[-1]: 'chaz_correct'})

        # get state name
        st = file[0:2]

        # add state and chamber columns
        df['state_po'] = st
        df['office'] = chamber

        # remove all irrelevant columns
        df = df[['state_po', 'office', 'NAME', 'chaz_correct']]

        # append to dfs
        dfs.append(df)

all_chaz_results = pd.concat(dfs)

results = pd.merge(all_chaz_results, results, how='right',
                   on=['state_po', 'office', 'NAME'])

corr_col = 'correctness_conflict'
results[corr_col] = results.apply(lambda x: x['chaz_correct'] == 'Correct' and
                                  x['correct'] == False or
                                  x['chaz_correct'] == 'Incorrect' and
                                  x['correct'] == True, axis=1)

# merge in densities
results = results.rename(columns={'GEOID': 'geoid'})
upper = results[results['office'] == 'upper'].copy()
lower = results[results['office'] == 'lower'].copy()
fips_path = money_path + 'foundation/raw/state_fips.csv'
fips_df = pd.read_csv(fips_path)
density_path = money_path + 'density/clean/'
upper, lower = merge_densities(fips_df, density_path, upper, lower)
results = pd.concat([upper, lower])

# merge in comments and races to ignore due to weird candiadate cases
comments = pd.read_csv(money_path + 'chaz/manual_ignore.csv', dtype=str)
results = pd.merge(results, comments, how='left', on=['geoid', 'office'])

results.to_csv(money_path + '/chaz/chaz_with_election_results.csv',
               index=False)
