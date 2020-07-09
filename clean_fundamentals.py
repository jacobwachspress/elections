"""Cleaning relevant data for fundmantals estimate."""

import pandas as pd
import numpy as np


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
    return


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
