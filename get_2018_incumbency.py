"""Get incumbency for 2018 using a fuzzy match."""

import pandas as pd
import numpy as np
import titlecase as tc
from difflib import SequenceMatcher


def main():
    """Get incumbency for 2018."""
    # initialize paths
    money_path = 'G:/Shared drives/princeton_gerrymandering_project/Moneyball/'
    path = money_path + 'fundamentals/'
    state_path = money_path + 'state/'

    # Load 2016 election results
    df_lower = pd.read_csv(state_path + 'lower_with_old_results.csv')
    df_upper = pd.read_csv(state_path + 'upper_with_old_results.csv')

    # Load 2018 election results and hand checked incumbency
    df_18 = pd.read_csv(path + 'temp/results_18.csv')
    df_hand = pd.read_csv(path + 'clean/incumbency_2016_hand_checked.csv')

    # Add incumbency and save
    df_lower = get_incumbency(df_lower, df_18, df_hand)
    df_upper = get_incumbency(df_upper, df_18, df_hand, chamber='upper')

    # Save
    lower_path = path + 'clean/lower_chamber_incumbency_2018.csv'
    upper_path = path + 'clean/upper_chamber_incumbency_2018.csv'
    df_lower.to_csv(lower_path, index=False)
    df_upper.to_csv(upper_path, index=False)
    return


def get_incumbency(df, df_18, df_hand, chamber='lower'):
    """Calculate incumbency for a specific chamber.

    Arguments:
        df: 2016 election results

        df_18: 2018 election results

        df_hand: hand checked incumbency where fuzz match is unclear

        chamber: lower or upper
    """
    # Reduce to proper chamber
    df_18 = df_18[df_18['chamber'] == 'lower']
    df_hand = df_hand[df_hand['chamber'] == 'lower']

    # zfill district numbers
    df['district_num'] = df['district_num'].str.zfill(3)
    df_hand['district_num'] = df_hand['district_num'].str.zfill(3)

    # Reduce columns
    df['winner'] = df['2016_winner']
    df = df[['state', 'district_num', 'winner', 'geoid']]
    df_18 = df_18[['state', 'district_num', 'dem_cand', 'ind_cand',
                   'rep_cand']]
    df_hand = df_hand.drop('chamber', axis=1)

    # Merge winner and candidates
    df = df.merge(df_18)

    # Turn winner into first last and title case
    df['winner'] = df['winner'].apply(lambda x: str(x).split(','))
    df['winner'] = df['winner'].apply(lambda x: x[-1] + ' ' + x[0])
    df['winner'] = df['winner'].apply(lambda x: tc.titlecase(x))

    df = df.fillna('')

    # Get ratio for each column
    df['dem_ratio'] = df.apply(lambda r: similar(r['dem_cand'], r['winner']),
                               axis=1)
    df['ind_ratio'] = df.apply(lambda r: similar(r['ind_cand'], r['winner']),
                               axis=1)
    df['rep_ratio'] = df.apply(lambda r: similar(r['rep_cand'], r['winner']),
                               axis=1)

    df['incumbent'] = df.apply(lambda r: incumb_ratio(r['dem_ratio'],
                                                      r['ind_ratio'],
                                                      r['rep_ratio']),
                               axis=1)

    # Add hand checked incumbency
    df = df.merge(df_hand, how='left')
    df['orig_incumbent'] = df['incumbent']
    df['incumbent'] = df['hand_incumbent'].fillna(df['incumbent'])
    df = df.drop_duplicates(subset=['state', 'district_num'])
    return df


def similar(a, b):
    """Fuzzy match."""
    return SequenceMatcher(None, a, b).ratio()


def incumb_ratio(dem, ind, rep):
    """Determine the party of the incumbent if they exist."""
    if dem >= 0.7 and dem > ind and dem > rep:
        return 'D'
    elif ind >= 0.7 and ind > rep:
        return 'I'
    elif rep >= 0.7:
        return 'R'
    else:
        return False


if __name__ == "__main__":
    main()
