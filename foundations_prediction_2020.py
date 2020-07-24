"""Calculate incumbency advantage in each district."""
import pandas as pd
import numpy as np


def main():
    money_path = 'G:/Shared drives/princeton_gerrymandering_project/Moneyball/'
    path = money_path + 'foundation/'

    # Get statewide presidential results and economist forecast
    df_state = pd.read_csv(path + 'clean/state_pres_results.csv')
    economist_path = money_path + 'elections/'
    economist_path += 'economist_projected_margins_most_recent.csv'
    df_econ = pd.read_csv(economist_path)

    # Get cleaned moneyball data
    df_lower = pd.read_csv(money_path + 'state/lower_input_data.csv')
    df_upper = pd.read_csv(money_path + 'state/upper_input_data.csv')

    # Load election results
    df_elec_18 = pd.read_csv(path + 'clean/election_results_2018.csv')

    # Convert 2018 results to dem voteshare
    df_16 = pd.read_csv(money_path + 'state/upper_chamber_results_2016.csv')
    df_elec_lower, df_elec_upper = results_to_dem_voteshare(df_elec_18, df_16)
    df_elec_lower.to_csv(path + 'temp/lower_voteshare.csv', index=False)
    df_elec_upper.to_csv(path + 'temp/upper_voteshare.csv', index=False)

    # Get difference between 2018 election and foundation prediction
    df_lower_resid = pd.read_csv(path + 'clean/imputed_sldl_residuals.csv')
    df_upper_resid = pd.read_csv(path + 'clean/imputed_sldu_residuals.csv')
    df_diff_lower = foundation_diff(df_state, df_lower_resid, df_elec_lower)
    df_diff_upper = foundation_diff(df_state, df_upper_resid, df_elec_upper)
    df_diff_lower.to_csv(path + 'temp/fund_diff_lower.csv', index=False)
    df_diff_upper.to_csv(path + 'temp/fund_diff_upper.csv', index=False)

    # Get foundation prediction
    df_proj_lower = foundation_prediction(df_lower, df_econ, df_diff_lower)
    df_proj_upper = foundation_prediction(df_upper, df_econ, df_diff_upper)
    df_proj_lower.to_csv(path + 'clean/proj_lower_2020.csv', index=False)
    df_proj_upper.to_csv(path + 'clean/proj_upper_2020.csv', index=False)

    return


def results_to_dem_voteshare(df, df_16):
    """Convert 2018 election results to dem voteshare.

    We assume that independents would caucus with the opposite party or else
    they would not be running.
        Note: if this is not true, we need to incorporate a way to change
              impute that the election is uncontested

    If a candidate gets more than 80% of the 3 party voteshare, we assume it is
    uncontested or essentially uncontested because the oppositing candidate is
    not representative of actual competition

    Impute independent votes for losing party if losing party did not have a
    candidate

    Arguments:
        df: 2018 election results.

        df_16: 2016 senate election results for KS and MN. They elect all
               state senators every 4 years

    Output:
        df_lower: cleaned dataframe for lower chambers

        df_upper: cleaned dataframe for upper chambers
    """
    # Reduce vote count names
    df['D'] = df['democrat']
    df['R'] = df['republican']
    df['I'] = df['independent']
    df = df.drop(columns=['democrat', 'republican', 'independent', 'year',
                          'dem_two', 'rep_two', 'district'])

    # Add 2016 upper chambers in MN and KS
    df_16['chamber'] = 'upper'
    df_16['D'] = df_16['dem']
    df_16['R'] = df_16['rep']
    df_16['I'] = df_16['other']
    df_16['three_sum'] = df_16['D'] + df_16['R'] + df_16['I']
    df_16['dem_three'] = df_16['D'] / df_16['three_sum']
    df_16['ind_three'] = df_16['I'] / df_16['three_sum']
    df_16['rep_three'] = df_16['R'] / df_16['three_sum']
    df_16 = df_16.drop(columns=['dem', 'rep', 'other', 'three_sum'])
    df_16['district_num'] = df_16['district_num'].astype(str).str.zfill(3)
    df = df.append(df_16)

    # Fix Alaska tie
    df.loc[(df['state'] == 'AK') & (df['district_num'] == '001'), 'R'] += 1

    # Get winning party (fix AK tie)
    df['win_party'] = df[['D', 'R', 'I']].idxmax(axis=1)

    # Get whether it was essentially uncontested
    df['max_three'] = df[['dem_three', 'rep_three', 'ind_three']].max(axis=1)
    df['uncontested'] = df['max_three'] >= 0.75
    df = df.drop('max_three', axis=1)

    # Get the party that got the least amount of votes
    df['worst_party'] = df[['D', 'R', 'I']].idxmin(axis=1)

    # Add flag if independent was in top two
    df['I_top_two'] = df['worst_party'] != 'I'

    # Impute independent as opposite party if opposite party had no candidate
    df['D'] = df.apply(lambda r: r['I'] if ((r['win_party'] == 'R') &
                                            (r['D'] == 0)) else r['D'], axis=1)
    df['R'] = df.apply(lambda r: r['I'] if ((r['win_party'] == 'D') &
                                            (r['R'] == 0)) else r['R'], axis=1)

    # Get two party voteshare
    df['dem_elec'] = df['D'] / (df['R'] + df['D'])

    # Split into lower and upper
    df_lower = df[df['chamber'] == 'lower']
    df_upper = df[df['chamber'] == 'upper']

    # Keep relevant columns
    keep_cols = ['state', 'district_num', 'win_party', 'I_top_two',
                 'uncontested', 'dem_elec']
    df_lower = df_lower[keep_cols]
    df_upper = df_upper[keep_cols]
    return df_lower, df_upper


def foundation_diff(df_state, df, df_elec):
    """Difference between election outcome and 2018 foundation prediction.

    Arguments:
        df_state: 2016 state presidential election results

        df: lower/upper chamber presidential election residuals

        df_elec: lower/upper chamber dem voteshare results in 2018
    """
    # Remove unnecessary columns from state
    df_state = df_state.drop(columns=['dem_12', 'rep_12', 'rep_16'])
    df_state.columns = ['state', 'dem_state']

    # Remove unnecesary columns from elections
    elec_cols = ['state', 'district_num', 'dem_elec', 'uncontested']
    df_elec = df_elec[elec_cols]

    # Join statewide voteshare to each prediction
    df = df.merge(df_state)
    df['no_incumb_pred'] = df['resid'] + df['dem_state']

    # Keep relevant columns
    keep_cols = ['state', 'geoid', 'district_num', 'resid', 'no_incumb_pred']
    df = df[keep_cols]

    # Merge with election data
    df = df.merge(df_elec, how='left')

    # Get difference between election and prediciton
    df['elec_diff'] = df['dem_elec'] - df['no_incumb_pred']

    # If uncontested let the election be a 30 point swing
    df.loc[(df['uncontested']) & (df['dem_elec'] > 0.5), 'elec_diff'] = 0.3
    df.loc[(df['uncontested']) & (df['dem_elec'] <= 0.5), 'elec_diff'] = -0.3

    # Impute average election difference by state
    df_state = df.groupby('state')['elec_diff'].mean()
    df_state = pd.DataFrame(df_state).reset_index()
    df_state.columns = ['state', 'state_diff']

    # Join state difference
    df = df.merge(df_state)

    # Get the result in 2018
    df['elec_18'] = df['dem_elec']

    # Keep relevant columns
    keep_cols = ['geoid', 'resid', 'elec_18', 'elec_diff', 'state_diff']
    df = df[keep_cols]
    return df


def foundation_prediction(df, df_econ, df_diff):
    """Get two party voteshare predictions using foundation model.

    Statewide economist forecast + district presidential residual + incumbency
    effect

    Arguments:
        df: lower/upper chamber cleaned moneyball data

        df_econ: current economist forecast

        df_diff: difference between 2018 results and no incumbency foundation
                 projected"""
    # Reduce economist data and adjust projected margin to dem voteshare
    df_econ = df_econ[['state', 'margin']]
    df_econ.columns = ['state', 'state_margin']
    df_econ['state_voteshare'] = df_econ['state_margin'] / 100 + 0.5

    # Join dataframes
    df = df.merge(df_econ).merge(df_diff)

    # Adjust state election difference in direction of incumbent
    df['state_diff'] = df.apply(lambda r: -r['state_diff']
                                if r['incumbent'] == 'R' else r['state_diff'],
                                axis=1)
    df.loc[df['incumbent'].isin(['I', 'False']), 'state_diff'] = 0

    # Calculate incumbency advantage elec_diff
    df['inc_adv'] = df['elec_diff'].fillna(df['state_diff'])

    # Calculate projected district voteshare w/o incumbency
    df['found_voteshare'] = df['state_voteshare'] + df['resid']

    # Add incumbency advantage
    df['is_inc'] = df['incumbent'].apply(lambda x: 1 if x in ['D', 'R'] else 0)
    df['found_voteshare'] += (df['is_inc'] * df['inc_adv'])

    # Clip voteshare between 0.7 and 0.3
    df['found_voteshare'] = np.clip(df['found_voteshare'], 0.3, 0.7)

    # Determine if we have results from a past election
    df['past_election'] = df['elec_diff'].notna()

    # Reduce to geoid and foundations voteshare
    df = df[['geoid', 'past_election', 'elec_18', 'found_voteshare']]
    return df


if __name__ == "__main__":
    main()
