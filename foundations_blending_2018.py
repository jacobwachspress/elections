"""Determine blending between Chaz and the Foundations model."""
import pandas as pd
import numpy as np

from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error as mse


def main():
    money_path = 'G:/Shared drives/princeton_gerrymandering_project/Moneyball/'
    path = money_path + 'foundation/clean/'

    # Hyperparameters
    uncontested_diff = 0.2
    foundations_clip = 0.1

    # Load state presidential results
    df_state = pd.read_csv(path + 'state_pres_results.csv')

    # Load chaz's 2018 predictions
    df_18 = pd.read_csv(money_path + 'chaz/chaz_with_election_results.csv')

    # Load historical results
    df_hist = pd.read_csv(money_path + 'state/all_input_data.csv')

    # Load residuals
    df_resid_lower = pd.read_csv(path + 'imputed_sldl_residuals.csv')
    df_resid_upper = pd.read_csv(path + 'imputed_sldu_residuals.csv')

    # Load incumbency
    incumb_str = '_chamber_incumbency_2016_2018.csv'
    df_inc_lower = pd.read_csv(path + 'lower' + incumb_str)
    df_inc_upper = pd.read_csv(path + 'upper' + incumb_str)

    # Compile all dataframes
    df = compile_data(df_18, df_hist, df_state, df_resid_lower, df_resid_upper,
                      df_inc_lower, df_inc_upper)

    # Get the incumbency advantage
    df = incumbency_advantage(df, uncontested_diff)

    # Get the foundations prediction
    df['found_share'] = df['dem_pres_16'] + df['inc_adv']
    df['found_share'] = np.clip(df['found_share'], 0.3, 0.7)

    # Get chaz voteshare
    df['chaz_share'] = df.apply(lambda r: chaz_share(r['favored'],
                                                     r['confidence']), axis=1)

    # Clip results
    df['dem_share_18'] = np.clip(df['dem_share_18'], 0.3, 0.7)
    df.to_csv(path + 'foundations_predictions_2018.csv', index=False)

    # Calculate blending
    df_blend = blend_predictions(df, foundations_clip)
    df_blend[df_blend['chamber'] == 'both']
    df_blend.to_csv(path + 'foundations_blending_results.csv', index=False)

    return


def clip_found(found, chaz, size):
    return np.clip(found, chaz - size, chaz + size)


def rmse(x, y):
    return np.round(np.sqrt(mse(x, y)), 4)


def chaz_share(party, confidence):
    """Turn prediction in to dem voteshare"""
    if confidence == 'Toss-Up':
        share = 0.5
    elif confidence == 'Tilt':
        share = 0.5 + .039 / 2
    elif confidence == 'Lean':
        share = 0.5 + 0.077 / 2
    elif confidence == 'Likely':
        share = 0.5 + 0.123 / 2
    elif confidence == 'Safe':
        share = 0.5 + 0.22 / 2
    else:
        share = 1

    # Flip voteshare if republican
    if party == 'R':
        return 1 - share

    # Else return the expected voteshare
    return share


def compile_data(df_18, df_hist, df_state, df_resid_lower, df_resid_upper,
                 df_inc_lower, df_inc_upper):
    """Compile all relevant data sources loaded into main.

    Arguments:
        df_18: chaz predictions from 2018 with election results

        df_20: chaz predictions from 2020 with 2016 election results

        df_state: state presidential election results

        df_resid_lower: lower chamber legislative district residual

        df_resid_upper: upper chamber legislative district residual

        df_inc_lower: lower chamber incumbency in 2018

        df_inc_upper: upper chamber incumbency in 2018
    """
    # Clean 2018 prediction and election data
    df_18['chamber'] = df_18['office']
    df_18['state'] = df_18['state_po']
    df_18['geoid'] = df_18['geoid'].astype(str).str.zfill(5)
    df_18['favored'] = df_18['predicted_winner']
    df_18.loc[df_18['win_party'] == 'R', 'win_margin'] *= -1
    df_18['dem_share_18'] = df_18['win_margin'] / 2 + 0.5
    keep_cols = ['state', 'geoid', 'chamber', 'confidence', 'favored',
                 'dem_share_18']
    df_18 = df_18[keep_cols]

    # Clean 2016 election data
    df_hist['chamber'] = df_hist['office']
    df_hist['geoid'] = df_hist['geoid'].astype(str).str.zfill(5)
    df_hist.loc[df_hist['2016_win_party'] == 'R',
                '2016_win_margin'] *= -1
    df_hist['dem_share_16'] = df_hist['2016_win_margin'] / 2 + 0.5
    df_hist.loc[df_hist['2014_win_party'] == 'R',
                '2014_win_margin'] *= -1
    df_hist['dem_share_14'] = df_hist['2014_win_margin'] / 2 + 0.5
    keep_cols = ['geoid', 'chamber', 'dem_share_16', 'dem_share_14']
    df_hist = df_hist[keep_cols]

    # Clean residuals
    keep_cols = ['geoid', 'resid']
    df_resid_lower = df_resid_lower[keep_cols]
    df_resid_upper = df_resid_upper[keep_cols]
    df_resid_lower['chamber'] = 'lower'
    df_resid_upper['chamber'] = 'upper'
    df_resid = df_resid_upper.append(df_resid_lower)
    df_resid['district_resid'] = df_resid['resid']
    df_resid['geoid'] = df_resid['geoid'].astype(str).str.zfill(5)
    df_resid = df_resid.drop('resid', axis=1)

    # Clean incumbency
    keep_cols = ['geoid', 'incumbent']
    df_inc_lower = df_inc_lower[keep_cols]
    df_inc_upper = df_inc_upper[keep_cols]
    df_inc_lower['chamber'] = 'lower'
    df_inc_upper['chamber'] = 'upper'
    df_inc = df_inc_upper.append(df_inc_lower)
    df_inc['geoid'] = df_inc['geoid'].astype(str).str.zfill(5)

    # Merge election data
    df = df_18.merge(df_hist, on=['geoid', 'chamber'], how='left')

    # Merge residuals
    df = df.merge(df_resid, on=['geoid', 'chamber'], how='left')
    df['district_resid'] = df['district_resid'].fillna(0)

    # Merge incumbency. Assume incumbent that is favored if unknown
    df = df.merge(df_inc, on=['geoid', 'chamber'], how='left')
    df['incumbent'] = df['incumbent'].fillna(df['favored'])

    # Merge statewide effects
    df_state = df_state.drop(columns=['dem_12', 'rep_12', 'rep_16'])
    df_state.columns = ['state', 'dem_state']
    df = df.merge(df_state)

    # Add 2016 presidentail result for the district
    df['dem_pres_16'] = df['dem_state'] + df['district_resid']
    return df


def incumbency_advantage(df, uncontested_diff):
    """Add the incumbency advantage for 2018 elections.

    Arguments:
        df: compiled dataframe

        uncontested_diff: what to assume the election difference
        is if a race is uncontested
    We will only use the 2016 election unless there
    was no election in that year in which we use the 2014 election.
    """
    # Get the last result
    df['dem_share_last'] = df['dem_share_18'].fillna(df['dem_share_16'])

    # Determine if the last election result was effectively uncontested
    df['uncontested'] = df['dem_share_last'] - 0.5
    df['uncontested'] = np.abs(df['uncontested']) > 0.25

    # Get the difference between the last election and 2016 nationwide partisan
    # nature of the district
    df['elec_diff'] = df['dem_share_last'] - df['dem_pres_16']

    # If uncontested set the election diffence to
    df.loc[(df['dem_share_last'] > 0.5) & (df['uncontested']),
           'elec_diff'] = uncontested_diff
    df.loc[(df['uncontested']) & (df['dem_share_last'] <= 0.5),
           'elec_diff'] = -uncontested_diff

    # Get the incumbency advantage
    df.loc[df['incumbent'].isin(['D', 'R']), 'inc_adv'] = df['elec_diff']
    df['inc_adv'] = df['inc_adv'].fillna(0)
    return df


def blend_instance(df):
    """Get individual blend between foundations and chaz."""
    df = df.dropna()
    X = df[['found_share', 'chaz_share']]
    y = df['dem_share_18']
    reg = LinearRegression(fit_intercept=False).fit(X, y)
    rmse_found = rmse(df['found_share'], df['dem_share_18'])
    rmse_chaz = rmse(df['chaz_share'], df['dem_share_18'])
    return reg.coef_[0], reg.coef_[1], rmse_found, rmse_chaz


def add_blend_results(df, rating, chamber, add_blend_results):
    """Add blending coefficient to dataframe."""
    r = len(df)
    df.at[r, 'rating'] = rating
    df.at[r, 'chamber'] = chamber
    df.at[r, 'found_coef'] = add_blend_results[0]
    df.at[r, 'chaz_coef'] = add_blend_results[1]
    df.at[r, 'found_rmse'] = add_blend_results[2]
    df.at[r, 'chaz_rmse'] = add_blend_results[3]
    return df


def blend_predictions(df, clip=0.1):
    """Get blending for Chaz's predictions.

    Arguments:
        df: dataframe with predictions

        clip: voteshare to clip foundations prediction around chaz
    """
    # Initialize blend dataframe
    df_blend = pd.DataFrame()

    # Clip foundations predictions around chaz predictions
    df['found_share'] = df.apply(lambda r: clip_found(r['found_share'],
                                                      r['chaz_share'],
                                                      clip), axis=1)

    # Keep blend columns
    df = df[['found_share', 'chaz_share', 'dem_share_18', 'confidence',
             'chamber']]

    # All both
    both = blend_instance(df)
    upper = blend_instance(df[df['chamber'] == 'upper'])
    lower = blend_instance(df[df['chamber'] == 'lower'])
    df_blend = add_blend_results(df_blend, 'all', 'both', both)
    df_blend = add_blend_results(df_blend, 'all', 'upper', upper)
    df_blend = add_blend_results(df_blend, 'all', 'lower', lower)

    # Non-Safe
    d = df[df['confidence'] != 'Safe']
    both = blend_instance(d)
    upper = blend_instance(d[d['chamber'] == 'upper'])
    lower = blend_instance(d[d['chamber'] == 'lower'])
    df_blend = add_blend_results(df_blend, 'Not Safe', 'both', both)
    df_blend = add_blend_results(df_blend, 'Not Safe', 'upper', upper)
    df_blend = add_blend_results(df_blend, 'Not Safe', 'lower', lower)

    # Individual
    for confidence in df.confidence.unique():
        d = df[df['confidence'] == confidence]
        both = blend_instance(d)
        upper = blend_instance(d[d['chamber'] == 'upper'])
        lower = blend_instance(d[d['chamber'] == 'lower'])
        df_blend = add_blend_results(df_blend, confidence, 'both', both)
        df_blend = add_blend_results(df_blend, confidence, 'upper', upper)
        df_blend = add_blend_results(df_blend, confidence, 'lower', lower)
    return df_blend



if __name__ == "__main__":
    main()
