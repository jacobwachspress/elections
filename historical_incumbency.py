"""Calculate Historical Incumbency."""

import pandas as pd
import titlecase as tc
from difflib import SequenceMatcher


def main():
    """Get historical incumbency unavailable in cnalysis rating."""
    # initialize paths
    money_path = 'G:/Shared drives/princeton_gerrymandering_project/Moneyball/'
    path = money_path + 'foundation/clean/'
    state_path = money_path + 'state/'
    elec_path = money_path + 'elections/'

    # Load 2016 election results
    df_lower = pd.read_csv(state_path + 'lower_input_data.csv')
    df_upper = pd.read_csv(state_path + 'upper_input_data.csv')

    # Load 2018 election results and hand checked incumbency
    df_18 = pd.read_csv(elec_path + 'election_results_2018.csv')
    df_hand_18 = pd.read_csv(path + 'incumbency_2016_2018_hand_checked.csv')

    # Add incumbency for whether 2018 candidate won in 2016
    df_lower_18 = get_incumbency_2018(df_lower, df_18, df_hand_18)
    df_upper_18 = get_incumbency_2018(df_upper, df_18, df_hand_18,
                                      chamber='upper')

    # Add incumbency for whether 2020 candidate won in 2016
    df_hand_16 = pd.read_csv(path + 'incumbency_2016_2020_hand_checked.csv')
    df_lower_16 = get_incumbency_2016(df_lower, df_hand_16)
    df_upper_16 = get_incumbency_2016(df_upper, df_hand_16)

    # Save
    lower_path_18 = path + 'lower_chamber_incumbency_2016_2018.csv'
    upper_path_18 = path + 'upper_chamber_incumbency_2016_2018.csv'
    lower_path_16 = path + 'lower_chamber_incumbency_2016_2020.csv'
    upper_path_16 = path + 'upper_chamber_incumbency_2016_2020.csv'
    df_lower_18.to_csv(lower_path_18, index=False)
    df_upper_18.to_csv(upper_path_18, index=False)
    df_lower_16.to_csv(lower_path_16, index=False)
    df_upper_16.to_csv(upper_path_16, index=False)
    return


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


def get_incumbency_2018(df, df_18, df_hand, chamber='lower'):
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


def get_incumbency_2016(df, df_hand, chamber='lower'):
    """Calculate incumbency for a specific chamber.

    Arguments:
        df: relevant chamber input data containing 2016 election results

        df_hand: hand checked incumbency where fuzz match is unclear

        chamber: lower or upper
    """
    # Reduce to main party incumbents in 2020 only
    df = df[df['incumbent'].isin(['D', 'R'])]

    # Get officeholder officeholder that is incumbent
    df['officeholder'] = ''
    df.loc[df['incumbent'] == 'R', 'officeholder'] = df['nom_R']
    df.loc[df['incumbent'] == 'D', 'officeholder'] = df['nom_D']

    # Remove asterisk from officeholder
    df['officeholder'] = df['officeholder'].apply(lambda x: x.replace('*', ''))

    # Reduce columns
    df['winner'] = df['2016_winner']
    df = df[['state', 'district_num', 'officeholder', 'incumbent', 'winner']]

    # Turn winner into first last and title case
    df['winner'] = df['winner'].apply(lambda x: str(x).split(','))
    df['winner'] = df['winner'].apply(lambda x: x[-1] + ' ' + x[0])
    df['winner'] = df['winner'].apply(lambda x: tc.titlecase(x))

    # Fill NaN with empty string for matching
    df = df.fillna('')

    # Get ratio for each column
    df['ratio'] = df.apply(lambda r: similar(r['officeholder'], r['winner']),
                           axis=1)
    df.loc[df['ratio'] >= 0.7, 'incumbent'] = df['incumbent']
    df.loc[df['ratio'] < 0.7, 'incumbent'] = False

    # Add hand checked incumbency
    df_hand = df_hand[df_hand['chamber'] == chamber]
    df = df.merge(df_hand, how='left')
    df['orig_incumbent'] = df['incumbent']
    df['incumbent'] = df['hand_incumbent'].fillna(df['incumbent'])
    df = df.drop_duplicates(subset=['state', 'district_num'])

    # Only keep relevant columns
    keep_cols = ['state', 'district_num', 'officeholder', 'winner',
                 'ratio', 'incumbent', 'orig_incumbent', 'hand_incumbent']
    df = df[keep_cols]
    return df


if __name__ == "__main__":
    main()
