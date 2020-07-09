"""Cleaning relevant data for fundmantals estimate."""

import pandas as pd
import numpy as np
import os
from clean_moneyball import massachusetts_cleaning
import difflib


def main():
    money_path = 'G:/Shared drives/princeton_gerrymandering_project/Moneyball/'
    path = money_path + 'fundamentals/'

    # Load and clean fips
    df_fips = pd.read_csv(path + 'raw/state_fips.csv')
    df_fips['fips'] = df_fips['fips'].astype(str).str.zfill(2)

    # Statewide presidential results
    df_state = pd.read_csv(path + 'raw/1976-2016-president.csv')
    df_state = get_statewide_presidential_results(df_state)
    df_state.to_csv(path + 'clean/state_pres_results.csv', index=False)

    # Presidential results by congressional district
    df_cd = pd.read_csv(path + 'raw/congressional_pvi.csv')
    df_cd = get_cong_dist_presidential_results(df_cd, df_fips)
    df_cd.to_csv(path + 'clean/cong_dist_pres_results.csv', index=False)

    # Get partisan residual of each congressional district
    df_cd_pr = get_cong_dist_partisan_residual(df_cd, df_state)
    df_cd_pr.to_csv(path + 'clean/cong_dist_partisan_residual.csv',
                    index=False)
    
    # Presidential results by st_leg district
    input_path = money_path + \
                    'fundamentals\\raw\\pres_results_by_state_leg_district\\'
    df_st_leg = get_all_st_leg_pres_results(input_path, df_fips)
    df_st_leg.to_csv(path + 'clean/st_leg_pres_results.csv', index=False)


def get_statewide_presidential_results(df):
    """Calculate 2-party voteshare in 2012 and 2016 for president by state.

    Arguments:
        df: MIT election lab presidential results
    """
    # reduce to democrat and republican
    df = df[df['party'].isin(['democrat', 'republican'])]

    # reduce to 2012 and 2016 elections
    df = df[df['year'].isin([2012, 2016])]

    # Remove writein votes
    df = df[~df['writein']]

    # Reduce columns
    df['state'] = df['state_po']
    df['votes'] = df['candidatevotes']
    df = df[['year', 'state', 'party', 'votes']]

    # Add minnesota 2012 obama votes
    r = len(df)
    df.at[r, 'year'] = 2012
    df.at[r, 'state'] = 'MN'
    df.at[r, 'party'] = 'democrat'
    df.at[r, 'votes'] = 1546167

    # Pivot the table
    df = pd.pivot_table(df, values='votes', index='state',
                        columns=['year', 'party'])

    # Update the columns
    df.columns = df.columns.droplevel()
    df.columns = ['dem_12', 'rep_12', 'dem_16', 'rep_16']

    # Reset the index
    df = df.reset_index()

    # Drop DC because it doesn't have legislatures
    df = df[df['state'] != 'DC']

    # Calculate two-party vote shares
    df['sum_12'] = df['dem_12'] + df['rep_12']
    df['sum_16'] = df['dem_16'] + df['rep_16']
    df['dem_12'] = df['dem_12'] / df['sum_12']
    df['rep_12'] = df['rep_12'] / df['sum_12']
    df['dem_16'] = df['dem_16'] / df['sum_16']
    df['rep_16'] = df['rep_16'] / df['sum_16']
    df = df.drop(columns=['sum_12', 'sum_16'])
    return df


def get_cong_dist_presidential_results(df, df_fips):
    """Calculate 2-party voteshare in 2012 and 2016 for pres by cong district.

    Arguments:
        df: Cook Political PVI by congressional district csv

        df_fips: dataframe w/ state abbreviations and fips codes
    """
    # Split original district into state and district number
    df['state'] = df['Dist'].apply(lambda x: x.split('-')[0])
    df['district_num'] = df['Dist'].apply(lambda x: x.split('-')[-1])
    df.loc[df['district_num'] == 'AL', 'district_num'] = '00'
    df['district_num'] = df['district_num'].str.zfill(2)

    # Add Fips
    df = df.merge(df_fips)

    # Add geoid
    df['geoid'] = df['fips'] + df['district_num']

    # Drop unnecesarry columns
    df = df.drop(columns=['Dist', 'Incumbent', 'PVI', 'fips'])

    # Rename columns
    df.columns = ['dem_16', 'rep_16', 'dem_12', 'rep_12', 'state',
                  'district_num', 'geoid']

    # Get two party voteshare
    df['sum_12'] = df['dem_12'] + df['rep_12']
    df['sum_16'] = df['dem_16'] + df['rep_16']
    df['dem_16'] /= df['sum_16']
    df['rep_16'] /= df['sum_16']
    df['dem_12'] /= df['sum_12']
    df['rep_12'] /= df['sum_12']

    # Sort columns
    df = df[['state', 'geoid', 'district_num', 'dem_12', 'rep_12', 'dem_16',
             'rep_16']]
    return df

def clean_st_leg_presidential_results(df, st_fips, chamber):
    """Calculate 2-party voteshare in 2012 and 2016 for pres for all
    state leg districts in a state.

    Arguments:
        df: election results by district, cleaned Daily Kos data

        st_fips: state fips code
        
        chamber: 'upper' or 'lower'
    """
    
    # Split original district into state and district number
    df['state'] = df['STATE']
            
    df['district_num'] = df['DISTRICT'].apply(lambda x: x.split(' ')[-1])
    df['district_num'] = df['district_num'].str.zfill(3)

    # Add Fips
    df['fips'] = st_fips

    # Add geoid
    df['geoid'] = df['fips'] + df['district_num']
    
    # Add chamber
    df['office'] = chamber
    
    # find columns we have for the 2012/2016 races
    important_cols = {'Clinton 2016 President D' : 'dem_16',\
                      'Trump 2016 President R' : 'rep_16',\
                      'Obama 2012 President D' : 'dem_12',\
                      'Romney 2012 President R' : 'rep_12'}
    cols_we_have = list(df.columns.intersection(important_cols))
    
    # string to int for results columns
    for col in cols_we_have:
        df[col] = df[col].apply(lambda x: int(x.replace(',', '')))

    # Drop unnecessary columns
    df = df[['state', 'geoid', 'office', 'district_num'] + cols_we_have]

    # Rename columns
    for col in cols_we_have:
        df[important_cols[col]] = df[col]
    
    # if we have the 2012 elections
    if 'dem_12' in df.columns and 'rep_12' in df.columns:
        
        # Get two party voteshare
        df['sum_12'] = df['dem_12'] + df['rep_12']
        df['dem_12'] /= df['sum_12']
        df['rep_12'] /= df['sum_12']
        
    # if we have the 2016 elections
    if 'dem_16' in df.columns and 'rep_16' in df.columns:
        
        # Get two party voteshare
        df['sum_16'] = df['dem_16'] + df['rep_16']
        df['dem_16'] /= df['sum_16']
        df['rep_16'] /= df['sum_16']


    # Drop unnecessary columns and sort to match format
    new_cols_we_have = list(df.columns.intersection(['dem_12', 'rep_12', \
                                                'dem_16', 'rep_16']))
    df = df[['state', 'geoid', 'office', 'district_num'] + new_cols_we_have]
    
    return df

    
def get_all_st_leg_pres_results(input_path, df_fips):
    ''' Reads in a bunch of files of state_leg presidential results by 
    state + chamber, cleans, and concats into one dataframe
    
    input_path: folder containing results by state+chamber
    
    df_fips: dataframe w/ state abbreviations and fips codes
    '''
    
    # store chambers that use multimember districts, to be ignored
    multimember_districts = {'upper' : ['VT', 'WV'], 'lower' : ['AZ', 'ID', \
                         'MD', 'NH', 'NJ', 'ND', 'SD', 'VT', 'WA', 'WV']}
    
    # initialize list of dfs to be concatenated
    dfs = []
    
    # for each state/chamber
    for file in os.listdir(input_path):
        
        # read in dataframe
        state_df = pd.read_csv(input_path+file)
        
        # get state, chamber, fips
        state = file[0:2]
        chamber = (file.split('_')[1])[:-4].lower()
        st_fips = df_fips.set_index('state').loc[state, 'fips']
        
        # check if this is a multimember district; if so, continue
        if state in multimember_districts[chamber]:
            continue
        
        # fix massachusetts
        if st_fips == '25':
            
            # prime for fuzzy match
            state_df['DISTRICT'] = state_df['DISTRICT'].apply(lambda x: \
                            'District ' + ' '.join(x.split(' ')[2:]))
            
            # grab dictionaries
            mass_dict_lower, mass_dict_upper, _, _ = massachusetts_cleaning()
            
            if chamber == 'lower':
                
                # fuzzy match to dict keys
                state_df['DISTRICT'] = state_df['DISTRICT'].apply(lambda x: \
                        difflib.get_close_matches(x, list(mass_dict_lower))[0])

                # change to numerical districts
                state_df['DISTRICT'] = state_df['DISTRICT'].apply(lambda x: \
                            str(mass_dict_lower[x]))
            else:

                # fuzzy match to dict keys
                state_df['DISTRICT'] = state_df['DISTRICT'].apply(lambda x: \
                        difflib.get_close_matches(x, list(mass_dict_upper))[0])

                # change to numerical districts
                state_df['DISTRICT'] = state_df['DISTRICT'].apply(lambda x: \
                            str(mass_dict_upper[x]))
                
        # clean dataframe and append to list
        dfs.append(clean_st_leg_presidential_results(state_df, st_fips, chamber))
        
        # merge all dfs
        out_df = pd.concat(dfs)
        
    # order columns appropriately and return
    return out_df[['state', 'office', 'geoid', 'district_num', 'dem_12', 
               'rep_12', 'dem_16', 'rep_16']]
        

def get_cong_dist_partisan_residual(df, df_state):
    """Calculate partisan residual for each congressional district.

    Partisan residual is defined as follows:

        Average of congressional district presidential vote in 2012 and 2016

        MINUS

        Average of statewide district presidential vote in 2012 and 2016

    Note that if we don't have 2012 data for a congressional district, we
    simply impute the 2016 result

    Arguments:
        df: cleaned congressional district presidential results

        df_state: cleaned statewide presidential results
    """
    # Impute 2012 voteshare with 2016 and vice versa
    df['dem_12'] = df['dem_12'].fillna(df['dem_16'])

    # Calculate average dem voteshare
    df['cd_dem'] = (df['dem_12'] + df['dem_16']) / 2
    df_state['state_dem'] = (df_state['dem_12'] + df_state['dem_16']) / 2

    # Reduce state to relevant columns
    df_state = df_state[['state', 'state_dem']]

    # Join state value to congressional districts
    df = df.merge(df_state)

    # Calculate congressional district residual
    df['resid'] = df['cd_dem'] - df['state_dem']

    # Reduce to relevant columns and save
    df = df[['state', 'geoid', 'district_num', 'resid']]
    return df


if __name__ == "__main__":
    main()
