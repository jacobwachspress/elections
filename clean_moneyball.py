"""Cleaning cnalysis and election results for State Leg. Moneyball Analysis."""

import pandas as pd
import numpy as np


def main():
    money_path = 'G:/Shared drives/princeton_gerrymandering_project/Moneyball/'
    path = money_path + 'state/'
    cvap_path = money_path + 'cvap/'

    # Initial cleaning
    df_lower = pd.read_csv(path + 'state_assembly.csv')
    df_lower = clean_initial_rating(df_lower)
    df_upper = pd.read_csv(path + 'state_senate.csv')
    df_upper = clean_initial_rating(df_upper)

    # Add recorded turnout
    df_election = pd.read_csv(path + 'state_overall_2018.csv',
                              encoding='ISO-8859-1')
    df_lower, df_upper = add_recorded_turnout(df_election, df_lower, df_upper)

    # Add cvap and cvap turnout estimate
    df_cvap_lower = pd.read_csv(cvap_path + 'SLDLC.csv')
    df_cvap_upper = pd.read_csv(cvap_path + 'SLDUC.csv')
    df_lower = add_cvap_turnout(df_lower, df_cvap_lower, df_election)
    df_upper = add_cvap_turnout(df_upper, df_cvap_upper, df_election)

    # Add upper KS and MN 2016 state senate turnout
    df_16 = pd.read_csv(path + 'upper_chamber_results_2016.csv')
    df_upper = add_2016_upper_races(df_upper, df_16)

    # Flag uncontested elections
    df_leg = pd.read_csv(path + 'pgp_state_leg_results.csv')
    df_lower = add_lower_uncontested(df_lower, df_leg)
    df_upper = add_upper_uncontested(df_upper)

    # Impute recorded turnout when no race / uncontested
    df_lower = add_turnout_estimate(df_lower)
    df_upper = add_turnout_estimate(df_upper)

    # Save datasets
    df_lower.to_csv(path + 'moneyball_lower_chamber.csv', index=False)
    df_upper.to_csv(path + 'moneyball_upper_chamber.csv', index=False)

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
        df: dataframe of cnalysis initial ratings
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
    df['incub_D'] = df['D NOM'].str.contains('[I]').fillna(False)
    df['incub_R'] = df['R NOM'].str.contains('[I]').fillna(False)
    df['incub_I'] = df['I NOM'].str.contains('[I]').fillna(False)

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


def massachussetts_cleaning():
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


def upper_uncontested():
    """Get districts in upper house that were previously uncontested."""
    d = {}

    d['AK'] = ['00C', '00O', '00S']

    d['AZ'] = ['003', '004', '019', '027', '029', '030']

    d['AR'] = ['006', '009', '015', '018', '020', '024', '030', '031']

    d['CO'] = []

    d['CT'] = ['002']

    d['FL'] = ['006', '030', '032', '038']

    d['GA'] = ['002', '005', '007', '008', '010', '011', '012', '013', '015',
               '018', '019', '020', '022', '023', '024', '025', '026', '028',
               '030', '031', '033', '035', '036', '039', '041', '042', '043',
               '044', '049', '050', '051', '053']

    d['HI'] = ['004', '007', '016', '023', '024']

    d['ID'] = ['006', '007', '009', '013', '018', '020', '023', '024', '025',
               '027', '030', '031', '032', '035']

    d['IL'] = ['002', '003', '005', '006', '008', '011', '012', '014', '015',
               '017', '018', '020', '039', '042', '044', '047', '050', '051',
               '053']

    d['IN'] = ['014', '019', '023', '039', '043']

    d['IA'] = ['001', '017', '031', '035', '045']

    d['KS'] = ['004', '022', '029']

    d['KY'] = ['010', '016']

    d['MA'] = []

    d['ME'] = []

    d['MN'] = ['046']

    d['MO'] = ['014']

    d['MT'] = ['008', '020', '030']

    d['NC'] = []

    d['ND'] = ['007', '009', '033', '039']

    d['NE'] = ['028', '034', '036', '046', '048']

    d['NV'] = ['010']

    d['NY'] = ['010', '012', '014', '018', '025', '027', '030', '035',
               '047', '048', '052', '057', '063']

    d['OH'] = []

    d['OK'] = ['010', '026', '034', '044', '046']

    d['OR'] = ['007', '017', '024']

    d['PA'] = ['002', '006', '014', '018', '042']

    d['RI'] = ['001', '002', '003', '004', '005', '006', '007', '010',
               '015', '016', '026', '029', '030', '037', '038']

    d['SC'] = []

    d['SD'] = ['001', '015']

    d['TN'] = ['001', '021', '003', '002', '033']

    d['TX'] = ['023']

    d['UT'] = []

    d['WA'] = ['013', '032', '034', '035', '048']

    d['WI'] = ['003', '011', '015', '033']

    d['WY'] = ['001', '005', '007', '009', '015', '019', '023', '027', '029']

    return d


def add_recorded_turnout(df, df_lower, df_upper):
    """Add the turnout recorded from 2018.

    Arguments:
        df: MEDSL election data

        df_lower: cleaned cnalysis data for lower chambers

        df_upper: cleaned cnalysis data for upper chambers
    """
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
    df['chamber'] = df['office'].apply(lambda x: 'upper' if x in senate_offices
                                       else 'lower')

    # Only get regular general elections and let the state be the abbreviation
    df = df[df['stage'] == 'gen']
    df = df[~df['special']]
    df['state'] = df['state_po']

    # Filter out WV, VT, and NH because of multi-member districts
    df = df[~df['state'].isin(['WV', 'VT', 'NH'])]

    # Drop duplicates according to the most recent version
    # Just use most votes for WA two races per district
    df = df.sort_values(by=['version', 'totalvotes'], ascending=[False, False])
    subset_cols = ['year', 'state', 'district', 'chamber']
    df = df.drop_duplicates(subset=subset_cols)

    # keep relevant columns
    keep_cols = ['year', 'state', 'state_fips', 'chamber', 'office',
                 'district', 'totalvotes']
    df = df[keep_cols]
    df = df.sort_values(by=['state', 'district'])

    # hardcoded cleaning (HI one-off and UT one-off matching errors)
    df['district'] = df['district'].apply(lambda x: 'District 19'
                                          if x == 'District 19 Vacancy' else x)
    df['district'] = df['district'].apply(lambda x: 'District 8'
                                          if x == 'District 8 (2 year term)'
                                          else x)

    # Get district number for MA
    mass_dict_L, mass_dict_U, _, _ = massachussetts_cleaning()
    df_ma = df[df['state'] == 'MA']
    df_ma_L = df_ma[df_ma['chamber'] == 'lower']
    df_ma_U = df_ma[df_ma['chamber'] == 'upper']
    df_ma_L['district_num'] = df_ma_L['district'].apply(lambda x:
                                                        str(mass_dict_L[x]))
    df_ma_U['district_num'] = df_ma_U['district'].apply(lambda x:
                                                        str(mass_dict_U[x]))

    # Get district num for every other state
    df = df[df['state'] != 'MA']
    df['district_num'] = df['district'].apply(lambda x: x.split(' ')[-1])

    # Append back together
    df_votes = df.append(df_ma_U).append(df_ma_L)
    df_votes['district_num'] = df_votes['district_num'].str.zfill(3)

    # Left join turnout and ratings for lower chambers
    df_lower_votes = df_votes[df_votes['chamber'] == 'lower']
    df_lower_votes = df_lower_votes[['state', 'district_num', 'totalvotes']]
    df_lower = df_lower.merge(df_lower_votes, on=['state', 'district_num'],
                              how='left')

    # Remove new mexico and new hampshire for senate analysis
    df_upper = df_upper[~df_upper['state'].isin(['NM', 'NH'])]

    # Left join turnout and ratings for upper chambers
    df_upper_votes = df_votes[df_votes['chamber'] == 'upper']
    df_upper_votes = df_upper_votes[['state', 'district_num', 'totalvotes']]
    df_upper = df_upper.merge(df_upper_votes, on=['state', 'district_num'],
                              how='left')
    return df_lower, df_upper


def add_cvap_turnout(df, df_cvap, df_elec):
    """Add CVAP to our moneyball dataset.

    Really rough and will need to be cleaned later

    Arguments:
        df: dataframe of lower or upper house after recorded turnout is added
        df_cvap: Census CVAP data for legislative districts
        df_elec: MEDSL 2018 election results
    """
    # Remove CA and DE b/c their MEDSL data is wrong
    df = df[~df['state'].isin(['CA', 'DE'])]

    # Only get totals
    df_cvap = df_cvap[df_cvap['lntitle'] == 'Total']

    # Only keep the name, geoid, and cvap estimate
    df_cvap = df_cvap[['geoname', 'geoid', 'cvap_est', 'cvap_moe']]
    df_cvap.columns = ['name', 'geoid', 'cvap', 'cvap_moe']

    # Get reduce the geoid and get the state name
    df_cvap['geoid'] = df_cvap['geoid'].apply(lambda x: x[-5:])
    df_cvap['state_fips'] = df_cvap['geoid'].apply(lambda x: x[:2])

    # Add the CVAP within the state and get the ratio
    df_state = pd.DataFrame(df_cvap.groupby('state_fips')['cvap'].sum())
    df_state = df_state.reset_index()
    df_state.columns = ['state_fips', 'cvap_state']
    df_cvap = df_cvap.merge(df_state)
    df_cvap['cvap_ratio'] = df_cvap['cvap'] / df_cvap['cvap_state']
    df_cvap = df_cvap[['geoid', 'cvap', 'cvap_moe', 'cvap_ratio']]

    # Convert state fips to a string and create district geoid
    df['state_fips'] = df['state_fips'].astype(str)
    df['geoid'] = df['state_fips'].str.zfill(2) + df['district_num']

    # Join cvap data to recorded turnout date
    df = df.merge(df_cvap, on='geoid')

    # Get max turnout
    df_elec = df_elec.groupby('state_po')['totalvotes'].max()
    df_elec = pd.DataFrame(df_elec).reset_index()
    df_elec.columns = ['state', 'statevotes']

    # merge max statewide turnout and estiamte cvap turnout
    df = df.merge(df_elec)
    df['turnout_cvap'] = np.round(df['cvap_ratio'] * df['statevotes'])

    # rename totalvotes to turnout_recorded and rename imputedvotes
    df['turnout_recorded'] = df['totalvotes']

    # Remove unnecessary columns
    df = df.drop(columns=['totalvotes', 'cvap_moe', 'statevotes'])
    return df


def add_lower_uncontested(df, df_leg):
    """Note which elections were uncontested previous cycle.

    Arguments:
        df: lower chamber dataframe

        df_leg: pgp state legislative election results"""

    # Clean legislative races to determine which are uncontested
    # Will adler imputed 100% for vote share if election was not contested
    df_leg = df_leg[df_leg['Year'] == 2018]
    df_leg['state'] = df_leg['State']
    df_leg['district_num'] = df_leg['District'].astype(str).str.zfill(3)
    df_leg['D'] = (df_leg['Dem Votes'] == 1)
    df_leg['R'] = (df_leg['GOP Votes'] == 1)
    df_leg['uncontested'] = (df_leg['D']) | (df_leg['R'])
    df_leg = df_leg[['state', 'district_num', 'uncontested']]
    df_leg.columns = ['state', 'district_num', 'prev_uncontested']

    # Join to lower chamber data
    df = df.merge(df_leg, how='left')

    # Impute False if there was no election
    df['prev_uncontested'] = df['prev_uncontested'].fillna(False)

    # We need to add previous uncontested elections not included in join
    mn_uncon = ['28A', '67A']
    _, _, ma_uncon, _ = massachussetts_cleaning()
    df.loc[(df['district_num'].isin(mn_uncon)) &
           (df['state'] == 'MN'), 'prev_uncontested'] = True
    df.loc[(df['district'].isin(ma_uncon)) &
           (df['state'] == 'MN'), 'prev_uncontested'] = True
    return df


def add_2016_upper_races(df_upper, df_elec):
    """Add 2016 upper chamber races for KS and MN.

    We do this because they did not have elections in 2018

    We also assume turnout decreases by 10% to put it on the midterm scale

    Arguments:
        df_upper:
            data on upper house chamber

        df_elec:
            election data
    """
    # Clean election dataframe
    df_elec['votes_16'] = df_elec['dem'] + df_elec['rep'] + df_elec['other']
    df_elec['district_num'] = df_elec['district_num'].astype(str).str.zfill(3)
    df_elec = df_elec[['state', 'district_num', 'votes_16']]
    df_elec['votes_16'] = np.round(0.9 * df_elec['votes_16']).astype(int)

    # Merge to upper dataframe
    df_upper = df_upper.merge(df_elec, how='left')

    # Set kansas and minnesota to have turnout recorded from 2016 results
    df_states = df_upper[df_upper['state'].isin(['KS', 'MN'])]
    df_states['turnout_recorded'] = df_states['votes_16']
    df_upper = df_upper[~df_upper['state'].isin(['KS', 'MN'])]
    df_upper = df_upper.append(df_states)
    df_upper = df_upper.drop('votes_16', axis=1)

    return df_upper


def add_upper_uncontested(df):
    """Denote which races were previously uncontested in upper chamber.

    Arguments:
        df: upper chamber dataframe
    """
    # Initialize uncontested to false
    df['prev_uncontested'] = False

    # Get district numbers of uncontested upper chambers
    uncon = upper_uncontested()

    # Iterate through each state
    for ix, elem in uncon.items():
        df.loc[(df['state'] == ix) &
               (df['district_num'].isin(elem)), 'prev_uncontested'] = True
    return df


def add_turnout_estimate(df):
    """Estimate turnout for all elections using imputation strategy.

    If there was recorded turnout set to that value

    If uncontested or no election use statewide turnout/cvap ratio

    Arguments:
        df: chamber dataframe
    """
    # Set recorded turnout to the initial estimate
    df['turnout_estimate'] = df['turnout_recorded']
    df.loc[df['prev_uncontested'], 'turnout_estimate'] = None

    # Get Set of Contested Races to Calculate Impuations
    df_rec = df[df['turnout_estimate'].notna()]

    # Calculate ratio of recorded turnout to cvap
    df_rec['rec_cvap_ratio'] = df_rec['turnout_recorded'] / df_rec['cvap']

    # Calculate the average ratio by state and add average of each state
    df_ratio = df_rec.groupby('state')['rec_cvap_ratio'].mean()
    df_ratio = pd.DataFrame(df_ratio).reset_index()
    df_ratio['rec_cvap_ratio_us'] = df_ratio['rec_cvap_ratio'].mean()

    # Join ratio to original dataframe and ensure all columns have U.S. mean
    df = df.merge(df_ratio, how='left')
    df['rec_cvap_ratio_us'] = df['rec_cvap_ratio_us'].mean()

    # Calculate turnout based on state ratio and us ratio
    df['turnout_state'] = np.round(df['rec_cvap_ratio'] * df['cvap'])
    df['turnout_us'] = np.round(df['rec_cvap_ratio_us'] * df['cvap'])

    # For the estimate impute state ratio estimate then us ratio estimate
    df['turnout_estimate'] = df['turnout_estimate'].fillna(df['turnout_state'])
    df['turnout_estimate'] = df['turnout_estimate'].fillna(df['turnout_us'])

    # Drop relevant columns
    drop_cols = ['rec_cvap_ratio', 'rec_cvap_ratio_us', 'turnout_state',
                 'turnout_us']
    df = df.drop(columns=drop_cols)
    return df


if __name__ == "__main__":
    main()
