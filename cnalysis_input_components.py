"""Cleaning cnalysis and election results for State Leg. Moneyball Analysis."""

import pandas as pd
import geopandas as gpd
import difflib


def main():
    
    # Initial cleaning
    lower = pd.read_csv('data/output/CNalysis/ratings_lower_chamber_' + \
                        'most_recent.csv') 
    lower = clean_initial_rating(lower)
    upper = pd.read_csv('data/output/CNalysis/ratings_upper_chamber_' + \
                        'most_recent.csv') 
    upper = clean_initial_rating(upper)

    # Fix incumbency errors in ratings
    incum_path = 'data/input/foundation/incumbent_corrections.csv'
    df_incumbent = pd.read_csv(incum_path)
    lower, upper = fix_incumbency(df_incumbent, lower, upper)

    # Add cvap by district
    df_cvap_lower = pd.read_csv('data/input/cvap/lower_chamber_cvap.csv')
    df_cvap_upper = pd.read_csv('data/input/cvap/upper_chamber_cvap.csv')
    lower = add_cvap(lower, df_cvap_lower)
    upper = add_cvap(upper, df_cvap_upper)

    # read in ordinals dict for massachusetts district name cleaning
    ordinals = pd.read_csv('data/input/general/ordinal_numbers.csv')
    ordinals['ordinal'] = ordinals['ordinal'].apply(lambda x: x.upper())
    ordinals_dict = dict(zip(ordinals['ordinal'], ordinals['number']))

    # merge in old election results
    df = pd.read_csv('data/input/election/st_leg_election_results_database.csv',
                                 dtype=str)

    upper, lower = merge_year_election_results(df, ordinals_dict, '2016',
                                               upper, lower)
    upper, lower = merge_year_election_results(df, ordinals_dict, '2014',
                                               upper, lower)
    upper, lower = merge_year_election_results(df, ordinals_dict, '2012',
                                               upper, lower)

    # get all fips
    fips_path = 'data/input/general/state_fips.csv'
    fips_df = pd.read_csv(fips_path)
    density_path = 'data/output/density/'

    # merge in densities
    upper, lower = merge_densities(fips_df, density_path, upper, lower)

    # merge incumbents
    lower_path = 'data/output/foundation/state_lower_chamber_incumbency.csv'
    upper_path = 'data/output/foundation/state_upper_chamber_incumbency.csv'
    lower_inc = pd.read_csv(lower_path)
    upper_inc = pd.read_csv(upper_path)
    lower_inc['district'] = lower_inc['district'].apply(lambda x:
                                                        str(int(x))
                                                        if type(x) == float
                                                        else str(x))
    upper_inc['district'] = upper_inc['district'].apply(lambda x:
                                                        str(int(x))
                                                        if type(x) == float
                                                        else str(x))
    upper, lower = merge_incumbents(upper, lower, upper_inc, lower_inc)

    # add columns for office
    lower['office'] = 'lower'
    upper['office'] = 'upper'

    # sort DataFrames
    upper = upper.sort_values(by=['state', 'geoid'])
    lower = lower.sort_values(by=['state', 'geoid'])

    # read out the cleaned files
    lower.to_csv('data/output/CNalysis/sldl_model_input_data.csv', index=False)
    upper.to_csv('data/output/CNalysis/sldu_model_input_data.csv', index=False)
    all_data = pd.concat([upper, lower])
    all_data.to_csv('data/output/CNalysis/all_input_data.csv', index=False)

    return


def get_incumb(d, r, i):
    """Determine the party of the incumbent if there is one.

    Arguments:
        d, r, and i are booleans of whether there is an incubment of
        that party
    """
    if d:
        return 'D'
    elif r:
        return 'R'
    elif i:
        return 'I'
    else:
        return False


def clean_initial_rating(df):
    """Preprocessing for moneyball

    Put ratings into cleaner format. We end up with the following attributes:
        state, state_fips, district, district_num, incumbent, flip, favored,
        confidence, nom_R, nom_D, nom_I

    If there is no incumbent entry is False
    If race is a toss-up favored is False

    Arguments:
        df: DataFrame of cnalysis initial ratings
    """
    # Extract if we expect a change and which party is favored
    df['flip'] = df['FLIP'].notna()
    df['favored'] = df['RATING'].apply(lambda x: x.split(' ')[-1])
    df['favored'] = df['favored'].apply(lambda x: False if x == 'Toss-Up'
                                        else x)
    df['confidence'] = df['RATING'].apply(lambda x: x.split(' ')[0])

    # If there is no election fix the confidence and favored
    df.loc[(df['favored'] == 'Election'), 'favored'] = False
    df.loc[(df['confidence'] == 'No'), 'confidence'] = False

    # Remove states with multi-member districts
    df = df[~df['STATE'].isin(['VT', 'WV'])]

    # Get if there is an incumbent
    df['incub_D'] = df['D NOM'].apply(lambda x: '[I]' in str(x))
    df['incub_R'] = df['R NOM'].apply(lambda x: '[I]' in str(x))
    df['incub_I'] = df['I NOM'].apply(lambda x: '[I]' in str(x))

    # Get which incumbent
    df['incumbent'] = df.apply(lambda r: get_incumb(r['incub_D'], r['incub_R'],
                                                    r['incub_I']), axis=1)
    df = df.drop(columns=['incub_D', 'incub_R', 'incub_I'])

    # Get state and district as lowercase as well as nominees
    df['state'] = df['STATE']
    df['district'] = df['DISTRICT']
    df['nom_R'] = df['R NOM'].fillna(False)
    df['nom_D'] = df['D NOM'].fillna(False)
    df['nom_I'] = df['I NOM'].fillna(False)
    df['nom_R'] = df['nom_R'].apply(lambda x: False if not x else
                                    x.split(' [I]')[0])
    df['nom_D'] = df['nom_D'].apply(lambda x: False if not x else
                                    x.split(' [I]')[0])
    df['nom_I'] = df['nom_I'].apply(lambda x: False if not x else
                                    x.split(' [I]')[0])

    # If your party is favored and the nominee is TBA assume that the primary
    # hasn't happened and there is an incumbent that will
    df.loc[(df['favored'] == 'R') & (df['nom_R'] == 'TBA') &
           (df['incumbent'] is False), 'incumbent'] = 'R'
    df.loc[(df['favored'] == 'D') & (df['nom_D'] == 'TBA') &
           (df['incumbent'] is False), 'incumbent'] = 'D'
    df.loc[(df['favored'] == 'I') & (df['nom_I'] == 'TBA') &
           (df['incumbent'] is False), 'incumbent'] = 'I'

    df.loc[(df['favored'] == 'R') & (df['R NOM'].isna()) &
           (df['incumbent'].astype(str) == 'False'), 'incumbent'] = 'R'
    df.loc[(df['favored'] == 'D') & (df['D NOM'].isna()) &
           (df['incumbent'].astype(str) == 'False'), 'incumbent'] = 'D'
    df.loc[(df['favored'] == 'I') & (df['I NOM'].isna()) &
           (df['incumbent'].astype(str) == 'False'), 'incumbent'] = 'I'

    # lowercase geoid
    df['geoid'] = df['GEOID'].str.zfill(5)
    df['state_fips'] = df['geoid'].apply(lambda x: x[:2])
    df['district_num'] = df['geoid'].apply(lambda x: x[2:])

    # Get relevant columns
    keep_cols = ['state', 'state_fips', 'district', 'district_num', 'geoid',
                 'incumbent', 'flip', 'favored', 'confidence', 'nom_R',
                 'nom_D', 'nom_I']
    df = df[keep_cols]

    return df


def massachusetts_cleaning():
    mass_dict_lower = {}
    mass_dict_upper = {}

    mass_dict_lower['District 1 Barnstable'] = 60
    mass_dict_lower['District 2 Barnstable'] = 61
    mass_dict_lower['District 3 Barnstable'] = 62
    mass_dict_lower['District 4 Barnstable'] = 63
    mass_dict_lower['District 5 Barnstable'] = 156

    mass_dict_lower['District 1 Berkshire'] = 65
    mass_dict_lower['District 2 Berkshire'] = 66
    mass_dict_lower['District 3 Berkshire'] = 67
    mass_dict_lower['District 4 Berkshire'] = 68

    mass_dict_lower['District 1 Bristol'] = 69
    mass_dict_lower['District 2 Bristol'] = 70
    mass_dict_lower['District 3 Bristol'] = 71
    mass_dict_lower['District 4 Bristol'] = 72
    mass_dict_lower['District 5 Bristol'] = 73
    mass_dict_lower['District 6 Bristol'] = 74
    mass_dict_lower['District 7 Bristol'] = 75
    mass_dict_lower['District 8 Bristol'] = 76
    mass_dict_lower['District 9 Bristol'] = 77
    mass_dict_lower['District 10 Bristol'] = 78
    mass_dict_lower['District 11 Bristol'] = 79
    mass_dict_lower['District 12 Bristol'] = 80
    mass_dict_lower['District 13 Bristol'] = 81
    mass_dict_lower['District 14 Bristol'] = 82

    mass_dict_lower['District 1 Essex'] = 83
    mass_dict_lower['District 2 Essex'] = 84
    mass_dict_lower['District 3 Essex'] = 85
    mass_dict_lower['District 4 Essex'] = 86
    mass_dict_lower['District 5 Essex'] = 87
    mass_dict_lower['District 6 Essex'] = 88
    mass_dict_lower['District 7 Essex'] = 89
    mass_dict_lower['District 8 Essex'] = 90
    mass_dict_lower['District 9 Essex'] = 91
    mass_dict_lower['District 10 Essex'] = 92
    mass_dict_lower['District 11 Essex'] = 93
    mass_dict_lower['District 12 Essex'] = 94
    mass_dict_lower['District 13 Essex'] = 95
    mass_dict_lower['District 14 Essex'] = 96
    mass_dict_lower['District 15 Essex'] = 97
    mass_dict_lower['District 16 Essex'] = 98
    mass_dict_lower['District 17 Essex'] = 99
    mass_dict_lower['District 18 Essex'] = 114

    mass_dict_lower['District 1 Franklin'] = 100
    mass_dict_lower['District 2 Franklin'] = 101

    mass_dict_lower['District 1 Hampden'] = 102
    mass_dict_lower['District 2 Hampden'] = 103
    mass_dict_lower['District 3 Hampden'] = 104
    mass_dict_lower['District 4 Hampden'] = 105
    mass_dict_lower['District 5 Hampden'] = 106
    mass_dict_lower['District 6 Hampden'] = 107
    mass_dict_lower['District 7 Hampden'] = 108
    mass_dict_lower['District 8 Hampden'] = 109
    mass_dict_lower['District 9 Hampden'] = 110
    mass_dict_lower['District 10 Hampden'] = 111
    mass_dict_lower['District 11 Hampden'] = 112
    mass_dict_lower['District 12 Hampden'] = 113

    mass_dict_lower['District 1 Hampshire'] = 115
    mass_dict_lower['District 2 Hampshire'] = 116
    mass_dict_lower['District 3 Hampshire'] = 117

    mass_dict_lower['District 1 Middlesex'] = 118
    mass_dict_lower['District 2 Middlesex'] = 119
    mass_dict_lower['District 3 Middlesex'] = 120
    mass_dict_lower['District 4 Middlesex'] = 121
    mass_dict_lower['District 5 Middlesex'] = 122
    mass_dict_lower['District 6 Middlesex'] = 123
    mass_dict_lower['District 7 Middlesex'] = 124
    mass_dict_lower['District 8 Middlesex'] = 125
    mass_dict_lower['District 9 Middlesex'] = 126
    mass_dict_lower['District 10 Middlesex'] = 127
    mass_dict_lower['District 11 Middlesex'] = 128
    mass_dict_lower['District 12 Middlesex'] = 129
    mass_dict_lower['District 13 Middlesex'] = 130
    mass_dict_lower['District 14 Middlesex'] = 131
    mass_dict_lower['District 15 Middlesex'] = 132
    mass_dict_lower['District 16 Middlesex'] = 133
    mass_dict_lower['District 17 Middlesex'] = 134
    mass_dict_lower['District 18 Middlesex'] = 135
    mass_dict_lower['District 19 Middlesex'] = 136
    mass_dict_lower['District 20 Middlesex'] = 137
    mass_dict_lower['District 21 Middlesex'] = 138
    mass_dict_lower['District 22 Middlesex'] = 139
    mass_dict_lower['District 23 Middlesex'] = 140
    mass_dict_lower['District 24 Middlesex'] = 141
    mass_dict_lower['District 25 Middlesex'] = 142
    mass_dict_lower['District 26 Middlesex'] = 143
    mass_dict_lower['District 27 Middlesex'] = 144
    mass_dict_lower['District 28 Middlesex'] = 145
    mass_dict_lower['District 29 Middlesex'] = 146
    mass_dict_lower['District 30 Middlesex'] = 147
    mass_dict_lower['District 31 Middlesex'] = 148
    mass_dict_lower['District 32 Middlesex'] = 149
    mass_dict_lower['District 33 Middlesex'] = 150
    mass_dict_lower['District 34 Middlesex'] = 151
    mass_dict_lower['District 35 Middlesex'] = 152
    mass_dict_lower['District 36 Middlesex'] = 153
    mass_dict_lower['District 37 Middlesex'] = 154

    mass_dict_lower['District 1 Norfolk'] = 157
    mass_dict_lower['District 2 Norfolk'] = 158
    mass_dict_lower['District 3 Norfolk'] = 159
    mass_dict_lower['District 4 Norfolk'] = 160
    mass_dict_lower['District 5 Norfolk'] = 161
    mass_dict_lower['District 6 Norfolk'] = 162
    mass_dict_lower['District 7 Norfolk'] = 163
    mass_dict_lower['District 8 Norfolk'] = 164
    mass_dict_lower['District 9 Norfolk'] = 165
    mass_dict_lower['District 10 Norfolk'] = 166
    mass_dict_lower['District 11 Norfolk'] = 167
    mass_dict_lower['District 12 Norfolk'] = 168
    mass_dict_lower['District 13 Norfolk'] = 169
    mass_dict_lower['District 14 Norfolk'] = 170
    mass_dict_lower['District 15 Norfolk'] = 171
    mass_dict_lower['District 16 Norfolk'] = 172
    mass_dict_lower['District 17 Norfolk'] = 173
    mass_dict_lower['District 18 Norfolk'] = 174

    mass_dict_lower['District 1 Plymouth'] = 172
    mass_dict_lower['District 2 Plymouth'] = 173
    mass_dict_lower['District 3 Plymouth'] = 174
    mass_dict_lower['District 4 Plymouth'] = 175
    mass_dict_lower['District 5 Plymouth'] = 176
    mass_dict_lower['District 6 Plymouth'] = 177
    mass_dict_lower['District 7 Plymouth'] = 178
    mass_dict_lower['District 8 Plymouth'] = 179
    mass_dict_lower['District 9 Plymouth'] = 180
    mass_dict_lower['District 10 Plymouth'] = 181
    mass_dict_lower['District 11 Plymouth'] = 182
    mass_dict_lower['District 12 Plymouth'] = 183

    mass_dict_lower['District 1 Suffolk'] = 184
    mass_dict_lower['District 2 Suffolk'] = 185
    mass_dict_lower['District 3 Suffolk'] = 186
    mass_dict_lower['District 4 Suffolk'] = 187
    mass_dict_lower['District 5 Suffolk'] = 188
    mass_dict_lower['District 6 Suffolk'] = 189
    mass_dict_lower['District 7 Suffolk'] = 190
    mass_dict_lower['District 8 Suffolk'] = 191
    mass_dict_lower['District 9 Suffolk'] = 192
    mass_dict_lower['District 10 Suffolk'] = 193
    mass_dict_lower['District 11 Suffolk'] = 194
    mass_dict_lower['District 12 Suffolk'] = 195
    mass_dict_lower['District 13 Suffolk'] = 196
    mass_dict_lower['District 14 Suffolk'] = 197
    mass_dict_lower['District 15 Suffolk'] = 198
    mass_dict_lower['District 16 Suffolk'] = 199
    mass_dict_lower['District 17 Suffolk'] = 200
    mass_dict_lower['District 18 Suffolk'] = 201
    mass_dict_lower['District 19 Suffolk'] = 202

    mass_dict_lower['District 1 Worcester'] = 203
    mass_dict_lower['District 2 Worcester'] = 204
    mass_dict_lower['District 3 Worcester'] = 205
    mass_dict_lower['District 4 Worcester'] = 206
    mass_dict_lower['District 5 Worcester'] = 207
    mass_dict_lower['District 6 Worcester'] = 208
    mass_dict_lower['District 7 Worcester'] = 209
    mass_dict_lower['District 8 Worcester'] = 210
    mass_dict_lower['District 9 Worcester'] = 211
    mass_dict_lower['District 10 Worcester'] = 212
    mass_dict_lower['District 11 Worcester'] = 213
    mass_dict_lower['District 12 Worcester'] = 214
    mass_dict_lower['District 13 Worcester'] = 215
    mass_dict_lower['District 14 Worcester'] = 216
    mass_dict_lower['District 15 Worcester'] = 217
    mass_dict_lower['District 16 Worcester'] = 218
    mass_dict_lower['District 17 Worcester'] = 219
    mass_dict_lower['District 18 Worcester'] = 155

    mass_dict_lower['District Barnstable, Dukes a Nantucket'] = 64

    mass_dict_upper['District Hampden'] = 3
    mass_dict_upper['District Norfolk, Bristol a Middlesex'] = 17
    mass_dict_upper['District 1 Bristol a Plymouth'] = 37
    mass_dict_upper['District 2 Bristol a Plymouth'] = 38
    mass_dict_upper['District Norfolk, Bristol a Plymouth'] = 32
    mass_dict_upper['District 1 Essex'] = 19
    mass_dict_upper['District 2 Essex'] = 21
    mass_dict_upper['District 3 Essex'] = 22
    mass_dict_upper['District 1 Essex a Middlesex'] = 20
    mass_dict_upper['District 2 Essex a Middlesex'] = 18
    mass_dict_upper['District Hampshire, Franklin a Worcester'] = 6
    mass_dict_upper['District 1 Hampden a Hampshire'] = 7
    mass_dict_upper['District 2 Hampden a Hampshire'] = 5
    mass_dict_upper['District Worcester, Hampden, Hampshire a Middlesex'] = 8
    mass_dict_upper['District Berkshire, Hampshire a Franklin'] = 4
    mass_dict_upper['District 1 Middlesex'] = 13
    mass_dict_upper['District 2 Middlesex'] = 25
    mass_dict_upper['District 3 Middlesex'] = 16
    mass_dict_upper['District 4 Middlesex'] = 24
    mass_dict_upper['District 5 Middlesex'] = 23
    mass_dict_upper['District 1 Middlesex a Norfolk'] = 29
    mass_dict_upper['District 2 Middlesex a Norfolk'] = 15
    mass_dict_upper['District 1 Plymou a Bristol'] = 36
    mass_dict_upper['District 2 Plymou a Bristol'] = 35
    mass_dict_upper['District 1 Suffolk'] = 1
    mass_dict_upper['District 2 Suffolk'] = 2
    mass_dict_upper['District 1 Suffolk a Middlesex'] = 27
    mass_dict_upper['District 2 Suffolk a Middlesex'] = 28
    mass_dict_upper['District 1 Worcester'] = 10
    mass_dict_upper['District 2 Worcester'] = 11
    mass_dict_upper['District Plymou a Barnstable'] = 39
    mass_dict_upper['District Cape a Islands'] = 40
    mass_dict_upper['District Worcester a Middlesex'] = 9
    mass_dict_upper['District Bristol a Norfolk'] = 31
    mass_dict_upper['District Plymou a Norfolk'] = 34
    mass_dict_upper['District Worcester a Norfolk'] = 12
    mass_dict_upper['District Norfolk a Plymouth'] = 33
    mass_dict_upper['District Middlesex a Suffolk'] = 26
    mass_dict_upper['District Norfolk a Suffolk'] = 30
    mass_dict_upper['District Middlesex a Worcester'] = 14

    ma_uncon_lower = ['MA-HD-1st Berkshire', 'MA-HD-1st Bristol',
                      'MA-HD-1st Franklin', 'MA-HD-1st Hampshire',
                      'MA-HD-1st Middlesex', 'MA-HD-1st Norfolk',
                      'MA-HD-1st Suffolk', 'MA-HD-2nd Berkshire',
                      'MA-HD-2nd Suffolk', 'MA-HD-3rd Barnstable',
                      'MA-HD-3rd Berkshire', 'MA-HD-3rd Essex',
                      'MA-HD-3rd Middlesex', 'MA-HD-3rd Suffolk',
                      'MA-HD-4th Barnstable', 'MA-HD-4th Berkshire',
                      'MA-HD-4th Bristol', 'MA-HD-4th Hampden',
                      'MA-HD-4th Norfolk', 'MA-HD-4th Suffolk',
                      'MA-HD-5th Bristol', 'MA-HD-5th Hampden',
                      'MA-HD-5th Middlesex', 'MA-HD-5th Norfolk',
                      'MA-HD-6th Hampden', 'MA-HD-6th Middlesex',
                      'MA-HD-6th Norfolk', 'MA-HD-6th Plymouth',
                      'MA-HD-6th Suffolk', 'MA-HD-6th Worcester',
                      'MA-HD-7th Bristol', 'MA-HD-7th Essex',
                      'MA-HD-7th Hampden', 'MA-HD-7th Middlesex',
                      'MA-HD-7th Norfolk', 'MA-HD-7th Suffolk',
                      'MA-HD-8th Bristol', 'MA-HD-8th Essex',
                      'MA-HD-8th Hampden', 'MA-HD-8th Middlesex',
                      'MA-HD-8th Norfolk', 'MA-HD-8th Plymouth',
                      'MA-HD-8th Suffolk', 'MA-HD-9th Bristol',
                      'MA-HD-9th Hampden', 'MA-HD-9th Middlesex',
                      'MA-HD-9th Plymouth', 'MA-HD-9th Suffolk',
                      'MA-HD-9th Worcester', 'MA-HD-10th Bristol',
                      'MA-HD-10th Essex', 'MA-HD-10th Hampden',
                      'MA-HD-10th Middlesex', 'MA-HD-10th Suffolk',
                      'MA-HD-11th Bristol', 'MA-HD-11th Essex',
                      'MA-HD-11th Hampden', 'MA-HD-11th Middlesex',
                      'MA-HD-11th Plymouth', 'MA-HD-11th Suffolk',
                      'MA-HD-11th Worcester', 'MA-HD-12th Essex',
                      'MA-HD-12th Norfolk', 'MA-HD-12th Suffolk',
                      'MA-HD-12th Worcester', 'MA-HD-13th Bristol',
                      'MA-HD-13th Middlesex', 'MA-HD-13th Norfolk',
                      'MA-HD-13th Suffolk', 'MA-HD-13th Worcester',
                      'MA-HD-14th Bristol', 'MA-HD-14th Norfolk',
                      'MA-HD-14th Suffolk', 'MA-HD-14th Worcester',
                      'MA-HD-15th Middlesex', 'MA-HD-15th Norfolk',
                      'MA-HD-15th Suffolk', 'MA-HD-15th Worcester',
                      'MA-HD-16th Essex', 'MA-HD-16th Middlesex',
                      'MA-HD-16th Worcester', 'MA-HD-17th Essex',
                      'MA-HD-17th Middlesex', 'MA-HD-17th Suffolk',
                      'MA-HD-18th Middlesex', 'MA-HD-18th Suffolk',
                      'MA-HD-18th Worcester', 'MA-HD-19th Suffolk',
                      'MA-HD-20th Middlesex', 'MA-HD-21st Middlesex',
                      'MA-HD-23rd Middlesex', 'MA-HD-24th Middlesex',
                      'MA-HD-25th Middlesex', 'MA-HD-26th Middlesex',
                      'MA-HD-27th Middlesex', 'MA-HD-28th Middlesex',
                      'MA-HD-29th Middlesex', 'MA-HD-32nd Middlesex',
                      'MA-HD-33rd Middlesex', 'MA-HD-34th Middlesex',
                      'MA-HD-35th Middlesex', 'MA-HD-37th Middlesex',
                      'MA-HD-Barnstable, Dukes & Nantucket']

    ma_uncon_upper = ['MA-SD-First Bristol & Plymouth',
                      'MA-SD-First Essex & Middlesex',
                      'MA-SD-First Hampden & Hampshire',
                      'MA-SD-First Middlesex & Norfolk',
                      'MA-SD-First Plymouth & Bristol',
                      'MA-SD-First Suffolk',
                      'MA-SD-First Suffolk & Middlesex',
                      'MA-SD-First Worcester',
                      'MA-SD-Second Bristol & Plymouth',
                      'MA-SD-Second Essex',
                      'MA-SD-Second Middlesex',
                      'MA-SD-Second Hampden & Hampshire',
                      'MA-SD-Second Middlesex & Norfolk',
                      'MA-SD-Second Suffolk',
                      'MA-SD-Second Suffolk & Middlesex',
                      'MA-SD-Second Worcester',
                      'MA-SD-Third Essex',
                      'MA-SD-Third Middlesex',
                      'MA-SD-Fourth Middlesex',
                      'MA-SD-Berkshire, Hampshire, Franklin & Hampden',
                      'MA-SD-Hampden',
                      'MA-SD-Hampshire, Franklin & Worcester',
                      'MA-SD-Middlesex & Suffolk',
                      'MA-SD-Norfolk, Bristol & Plymouth',
                      'MA-SD-Norfolk & Suffolk']

    return mass_dict_lower, mass_dict_upper, ma_uncon_lower, ma_uncon_upper


def add_cvap(df, df_cvap):
    """Add CVAP to our moneyball dataset.

    Arguments:
        df: DataFrame of lower or upper house
        df_cvap: Census CVAP data for legislative districts
    """

    # Only get totals
    df_cvap = df_cvap[df_cvap['lntitle'] == 'Total']

    # Only keep the name, geoid, and cvap estimate
    df_cvap = df_cvap[['geoname', 'geoid', 'cvap_est']]
    df_cvap.columns = ['name', 'geoid', 'cvap']

    # Reduce the geoid
    df_cvap['geoid'] = df_cvap['geoid'].apply(lambda x: x[-5:])

    # Convert state fips to a string and create district geoid
    df['state_fips'] = df['state_fips'].astype(str)
    df['geoid'] = df['state_fips'].str.zfill(2) + df['district_num']

    # Join cvap data
    df = df.merge(df_cvap, on='geoid')

    return df


def fix_incumbency(df_incumbent, lower, upper):
    """Fix incumbency entry errors in Chaz's sheet.

    Arguments:
        df_incumbent: DataFrame to fix incumbent errros

        lower: lower chamber moneyball data

        upper: upper chamber moneyball data
    """
    # Set incumbent geoid to zfill
    df_incumbent['geoid'] = df_incumbent['geoid'].astype(str).str.zfill(5)

    # Update lower chamber incumbents
    for ix, row in df_incumbent[df_incumbent['chamber'] == 'lower'].iterrows():
        lower.loc[lower['geoid'] == row['geoid'],
                  'incumbent'] = row['actual_incumbent']

    # Update upper chamber incumbents
    for ix, row in df_incumbent[df_incumbent['chamber'] == 'upper'].iterrows():
        upper.loc[upper['geoid'] == row['geoid'],
                  'incumbent'] = row['actual_incumbent']

    return lower, upper


def merge_year_election_results(df, ordinals_dict, year, sldu_old, sldl_old):
    ''' Parses Klamer election results and cleans up results from a
    given year, merges to old DataFrames

    Arguments:
        df: election results df
        ordinals_dict: ANNOYING dictionary of {First:1, Second:2} etc. for
            massachusetts
        year: year_to_merge
        sldu_old, sldl_old: old DataFrames for merge on fips+district
    '''
    # remove "scattering" votes
    df = df[df['cand'] != 'scattering']

    # make vote totals floats
    df['vote'] = df['vote'].astype(float)

    # make party uppercase
    df['partyt'] = df['partyt'].apply(lambda x: x.upper())

    # makes fips a two-digit string
    df['sfips'] = df['sfips'].str.zfill(2)

    # keep only the year in question
    df = df[df['year'] == year]

    # keep only general elections done concurrently with other Nov. elections
    df = df[df['etype'] == 'g']

    # get upper and lower DataFrames
    upper_df = df[df['sen'] == '1'].copy()
    lower_df = df[df['sen'] == '0'].copy()

    # for both chamber DataFrames
    input_dfs = {'u': upper_df, 'l': lower_df}
    output_dfs = {}
    for i in input_dfs:

        cham_df = input_dfs[i]

        # get the cleanest form of district designation for match
        cham_df['ddez'] = cham_df.apply(lambda x:
                                        x['ddez'].replace('-', '')
                                        if x['sfips'] != '50'
                                        else x['ddez'], axis=1)

        # make district a three-digit string
        cham_df['ddez'] = cham_df['ddez'].str.zfill(3)

        # sort DataFrame so that the first instance of the candidate's party is
        # the party under which they received the most votes
        cham_df = cham_df.sort_values(by=['sid', 'ddez', 'cand', 'vote'],
                                      ascending=[True, True, True, False])
        # add votes for same candidate if multiple rows have their name
        grouped = cham_df.groupby(['sid', 'ddez', 'cand'])
        cham_df = grouped.agg({'vote': sum, 'sfips': 'first',
                               'outcome': 'first', 'partyt': 'first',
                               'sen': 'first'}).reset_index()

        # get total_votes in each race
        grouped = cham_df.groupby(['sid', 'ddez'])['vote']
        totalvotes = grouped.sum()
        totalvotes = totalvotes.reset_index()

        # rename column for better merge
        totalvotes = totalvotes.rename(columns={'vote': 'totalvotes'})

        # add totalvotes column to cham_df
        cham_df = pd.merge(cham_df, totalvotes, how='left', on=['sid', 'ddez'])

        """Make Function"""
        # get winning margins, using same grouped object
        winmargins = grouped.apply(lambda x: 1 if len(x) \
             < 2 else (x.nlargest(2).max() - x.nlargest(2).min()) / x.sum())
        winmargins = winmargins.reset_index()

        # rename column for better merge
        winmargins = winmargins.rename(columns={'vote': 'win_margin'})

        # add totalvotes column to cham_df
        cham_df = pd.merge(cham_df, winmargins, how='left', on=['sid', 'ddez'])

        # reduce DataFrame to winners
        # IF YOU AIN'T FIRST, YOU'RE LAST
        cham_df = cham_df[cham_df['outcome'] == 'w']

        # clean massachusetts
        mass_df = cham_df[cham_df['sfips'] == '25'].copy()
        mass_dict_lower, mass_dict_upper, _, _ = massachusetts_cleaning()

        # if upper
        if i == 'u':
            matching_dict = mass_dict_upper
        else:
            matching_dict = mass_dict_lower

        # prime dictionary for match
        capital_dict = {}
        for j in matching_dict:
            capital_dict[j.upper()] = matching_dict[j]

        # prime DataFrame for match
        mass_df['ddez'] = mass_df['ddez'].apply(lambda x:
                                                'DISTRICT ' + x.upper())

        # change ordinal numbers to numerals
        # CAN'T DO FIRST, SECOND, ETC. FIRST OR YOU GET AN EVIL BUG LIKE
        # TWENTY1
        keys = list(ordinals_dict.keys())
        keys.reverse()
        for k in keys:
            mass_df['ddez'] = mass_df['ddez'].apply(lambda x: \
                   x.replace(k, str(ordinals_dict[k])))

        # fuzzy match to dict keys
        mass_df['ddez'] = mass_df['ddez'].apply(lambda x: \
                difflib.get_close_matches(x, list(capital_dict))[0])

        # change to numerical districts
        mass_df['ddez'] = mass_df['ddez'].apply(lambda x: \
                    str(capital_dict[x]).zfill(3))

        cham_df = cham_df[cham_df['sfips'] != '25']
        cham_df = pd.concat([cham_df, mass_df], sort=True)
        # columns to keep
        cols_to_keep = ['sfips', 'ddez', 'cand', 'vote', 'totalvotes',
                        'win_margin', 'partyt']

        cham_df = cham_df[cols_to_keep]

        # change column names to match
        cham_df.columns = ['state_fips', 'district_num', year + '_winner',
                           year + '_winner_vote', year + '_totalvotes',
                           year + '_win_margin', year + '_win_party']
        output_dfs[i] = cham_df

    # merge DataFrames
    upper = pd.merge(sldu_old, output_dfs['u'], how='left',
                     on=['state_fips', 'district_num'])
    lower = pd.merge(sldl_old, output_dfs['l'], how='left',
                     on=['state_fips', 'district_num'])

    return upper, lower


def merge_densities(fips_df, density_path, upper, lower):
    ''' Merges in density data to upper and lower DataFrames

    Arguments:
        fips_df: DataFrame with states and two-digit FIPS codes
        density_path: path where all density files are held, in the format
            density_path + chamber + '/' + state fips code + '_districts.shp'
        upper, lower: old DataFrames for merge on geoid
    '''

    # get all states to test
    all_fips = fips_df['fips'].astype(str).str.zfill(2).unique()

    # for each chamber
    for cham in ['upper', 'lower']:

        # initialize list of state DataFrames to concatenate at the end
        dfs = []

        # for each state
        for st_fips in all_fips:

            # nebraska lower does not exist, skip
            if st_fips == '31' and cham == 'lower':
                continue

            # read in density DataFrame
            density_df = gpd.read_file(density_path + cham + '/' + st_fips +
                                       '_districts.shp')

            # create geoid column from GEOID
            density_df['geoid'] = density_df['GEOID']

            # remove unnecessary columns
            density_df = density_df[['geoid', 'rural', 'exurban',
                                     'suburban', 'urban']]

            # append this to the list of DataFrames to concat
            dfs.append(density_df)

        # concatenate all state DataFrames
        to_merge = pd.concat(dfs)

        # get proportion of population in each density
        columns = ['rural', 'exurban', 'suburban', 'urban']
        to_merge['pop'] = to_merge[columns].sum(axis=1)
        for col in columns:
            to_merge[col + '_prop'] = to_merge[col] / to_merge['pop']

        # merge to appropriate chamber DataFrame
        if cham == 'upper':
            upper = pd.merge(upper, to_merge, how='left', on='geoid')
        else:
            lower = pd.merge(lower, to_merge, how='left', on='geoid')

    return upper, lower


def merge_incumbents(upper, lower, upper_inc, lower_inc):
    ''' Merges in incumbents from wikipedia scrape

    Arguments:
        upper, lower: original DataFrames
        upper_inc, lower_inc: DataFrames with incumbency info
    '''
    
    # clean district numbers
    upper_inc['district'] = upper_inc['district'].apply(lambda x:
                                                        str(x).zfill(3))

    lower_inc['district'] = lower_inc['district'].apply(lambda x:
                                                        str(x).zfill(3))

    # rename columns
    rename_cols = ['state', 'wiki_incumbent', 'inc_party', 'district_num']
    upper_inc.columns = rename_cols
    lower_inc.columns = rename_cols

    # merge DataFrames
    join_cols = ['state', 'district_num']
    upper = pd.merge(upper, upper_inc, how='left', on=join_cols)
    lower = pd.merge(lower, lower_inc, how='left', on=join_cols)

    # for each DataFrame
    for cham in [upper, lower]:

        # for each race
        for i, dist in cham.iterrows():

            # if no favorite is listed, this is a no-election seat, update to
            # uncontested and make the favored party the incumbent party
            if dist['confidence'] == False:
                if dist['incumbent'] == False:
                    cham.loc[i, 'incumbent'] = cham.loc[i, 'inc_party']
                cham.loc[i, 'favored'] = cham.loc[i, 'incumbent']
                cham.loc[i, 'confidence'] = 'Uncontested'

    return upper, lower


if __name__ == "__main__":
    main()
