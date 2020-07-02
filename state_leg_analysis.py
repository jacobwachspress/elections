# -*- coding: utf-8 -*-
"""
Created on Fri Jun  5 15:38:40 2020

@author: Jacob
"""

import pandas as pd

sts = ['TN','SC','MD','IN','VT','RI','FL','UT','CA','WV','GA','WY','NM',\
          'MO','MT','LA','CO','IL','NY','AK','NC','NE','OR','WA','MA','NV',\
          'MI','AR','CT','NH','OK','VA','OH','HI','AL','KY','IA','MS',\
          'WI','AZ','TX','SD','ME','ID','DE','NJ','MN','PA','ND','KS']

## DOWNLOADING RATINGS FROM CHAZ

def compile_ratings(in_file, out_file):

    df = pd.read_csv(in_file)

    ratings = set(df['RATING'])
    states = list(set(df['STATE']))

    new_df = pd.DataFrame()
    new_df['STATE'] = states
    new_df.set_index('STATE', inplace=True)

    for rating in ratings:
        new_df[rating] = ''

    new_df['SEATS'] = ''

    for state in states:
        state_df = df[df['STATE'] == state]

        for rating in ratings:
            new_df.loc[state, rating] = \
                len(state_df[state_df['RATING'] == rating])

        new_df.loc[state, 'SEATS'] = len(state_df)
        new_df.to_csv(out_file)

    return 1


## DO
    https://github.com/openelections/openelections-data-tx/tree/master/2018
