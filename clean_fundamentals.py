"""Cleaning relevant data for fundmantals estimate."""

import pandas as pd
import numpy as np


def main():
    money_path = 'G:/Shared drives/princeton_gerrymandering_project/Moneyball/'
    path = money_path + 'fundamentals/'

    # Initial cleaning
    df = pd.read_csv(path + 'raw/1976-2016-president.csv')
    df = get_statewide_presidential_results(df)
    df.to_csv(path + 'clean/statewide_presidential_results.csv')
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


if __name__ == "__main__":
    main()
