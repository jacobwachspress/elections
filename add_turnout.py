"""Rough script for adding turnout to Chaz's ratings. Needs to be cleaned."""
import pandas as pd
import numpy as np

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

df = pd.read_csv('Data/state/state_overall_2018.csv', encoding='ISO-8859-1')

# Filter to state assembly/senate offices
relevant_offices = ['House of Delegates Member', 'State Assembly Member',
                    'State Assembly Representative', 'State House Delegate',
                    'State Representative',
                    'State Representative (Partial Term Ending 01/01/2019)',
                    'State Representative A', 'State Representative B',
                    'State Representative Pos. 1',
                    'State Representative Pos. 2', 'State Senate',
                    'State Senator',
                    'State Senator Partial Term Ending (01/01/2019)']
senate_offices = ['State Senate', 'State Senator',
                  'State Senator Partial Term Ending (01/01/2019)']
df = df[df['office'].isin(relevant_offices)]

# Add chamber
df['chamber'] = df['office'].apply(lambda x: 'upper' if x in senate_offices
                                   else 'lower')

# Only get regular general elections
df = df[df['stage'] == 'gen']
df = df[~df['special']]
df['state'] = df['state_po']

# Filter out WV and VT
df = df[~df['state'].isin(['WV', 'VT', 'NH'])]
# Drop duplicates according to the most recent version
# Just use most votes for WA two races per district
df = df.sort_values(by=['version', 'totalvotes'], ascending=[False, False])
subset_cols = ['year', 'state', 'district', 'chamber']
df = df.drop_duplicates(subset=subset_cols)

# keep relevant columns
keep_cols = ['year', 'state', 'state_fips', 'chamber', 'office', 'district',
             'totalvotes']
df = df[keep_cols]
df = df.sort_values(by=['state', 'district'])

# hardcoded cleaning (HI one-off and UT one-off)
df['district'] = df['district'].apply(lambda x: 'District 19'
                                      if x == 'District 19 Vacancy' else x)
df['district'] = df['district'].apply(lambda x: 'District 8'
                                      if x == 'District 8 (2 year term)'
                                      else x)

# Get district number for MA
df_ma = df[df['state'] == 'MA']
df_ma_lower = df_ma[df_ma['chamber'] == 'lower']
df_ma_upper = df_ma[df_ma['chamber'] == 'upper']
df_ma_lower['district_num'] = df_ma_lower['district'].apply(lambda x: str(mass_dict_lower[x]))
df_ma_upper['district_num'] = df_ma_upper['district'].apply(lambda x: str(mass_dict_upper[x]))


# Get district num for every other state
df = df[df['state'] != 'MA']
df['district_num'] = df['district'].apply(lambda x: x.split(' ')[-1])

# Append back together
df_votes = df.append(df_ma_upper).append(df_ma_lower)
df_votes['district_num'] = df_votes['district_num'].str.zfill(3)

# Left join turnout and ratings
df = pd.read_csv('data/State/state_assembly_clean.csv')
df_lower = df_votes[df_votes['chamber'] == 'lower']
df_lower = df_lower[['state', 'district_num', 'totalvotes']]
df = df.merge(df_lower, on=['state', 'district_num'], how='left')

# Get mean turnout for each district
df_mean = pd.DataFrame(df.groupby('state')['totalvotes'].mean())
df_mean['totalvotes'] = np.round(df_mean['totalvotes']).astype(int)
df_mean.columns = ['meanvotes']
df = df.merge(df_mean, left_on='state', right_index=True)
df['imputedvotes'] = df['totalvotes'].isna()
df['totalvotes'] = df['totalvotes'].fillna(df['meanvotes'])
df = df.drop('meanvotes', axis=1)
df.to_csv('data/State/state_assembly_turnout.csv', index=False)

# Left join turnout and ratings
df = pd.read_csv('data/State/state_senate_clean.csv')
df = df[~df['state'].isin(['NM', 'NH'])]
df_lower = df_votes[df_votes['chamber'] == 'upper']
df_lower = df_lower[['state', 'district_num', 'totalvotes']]
df = df.merge(df_lower, on=['state', 'district_num'], how='left')

# Get mean turnout for each district
df_mean = pd.DataFrame(df.groupby('state')['totalvotes'].mean())
df_mean['totalvotes'] = np.round(df_mean['totalvotes']).astype(int)
df_mean.columns = ['meanvotes']
df = df.merge(df_mean, left_on='state', right_index=True)
df['imputedvotes'] = df['totalvotes'].isna()
df['totalvotes'] = df['totalvotes'].fillna(df['meanvotes'])
df = df.drop('meanvotes', axis=1)
df.to_csv('data/State/state_senate_turnout.csv', index=False)
