"""Calculate incumbency advantage in each district."""

import pandas as pd
import numpy as np
from clean_moneyball import massachusetts_cleaning


def main():
    money_path = 'G:/Shared drives/princeton_gerrymandering_project/Moneyball/'
    path = money_path + 'fundamentals/'

    # Get statewide presidential results and economist forecast
    df_state = pd.read_csv(path + 'clean/state_pres_results.csv')
    df_econ = pd.read_csv(money_path + 'economist/projected_margins_07_11.csv')

    # Get cleaned moneyball data
    df_lower = pd.read_csv(money_path + 'state/moneyball_lower_chamber.csv')
    df_upper = pd.read_csv(money_path + 'state/moneyball_upper_chamber.csv')

    # Clean 2018 Results
    df = pd.read_csv(money_path + 'state/state_overall_2018.csv',
                     encoding='ISO-8859-1')
    df_elec_18 = clean_results_18(df)
    df_elec_18.to_csv(path + 'temp/results_18.csv', index=False)

    # Convert 2018 results to dem voteshare
    df_16 = pd.read_csv(money_path + 'state/upper_chamber_results_2016.csv')
    df_elec_lower, df_elec_upper = results_to_dem_voteshare(df_elec_18, df_16)
    df_elec_lower.to_csv(path + 'temp/lower_voteshare.csv', index=False)
    df_elec_upper.to_csv(path + 'temp/upper_voteshare.csv', index=False)

    # Get difference between 2018 election and fundamentals prediction
    df_lower_resid = pd.read_csv(path + 'clean/imputed_sldl_residuals.csv',
                                 index_col=0)
    df_upper_resid = pd.read_csv(path + 'clean/imputed_sldu_residuals.csv',
                                 index_col=0)
    df_diff_lower = fundamentals_diff(df_state, df_lower_resid, df_elec_lower)
    df_diff_upper = fundamentals_diff(df_state, df_upper_resid, df_elec_upper)
    df_diff_lower.to_csv(path + 'temp/fund_diff_lower.csv', index=False)
    df_diff_upper.to_csv(path + 'temp/fund_diff_upper.csv', index=False)

    # Get fundamentals prediction
    df_proj_lower = fundamentals_prediction(df_lower, df_econ, df_diff_lower)
    df_proj_upper = fundamentals_prediction(df_upper, df_econ, df_diff_upper)
    df_proj_lower.to_csv(path + 'clean/proj_lower_2020.csv', index=False)
    df_proj_upper.to_csv(path + 'clean/proj_upper_2020.csv', index=False)
    return


def clean_results_18(df):
    """Clean MIT electin lab election results in 2018."""
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

    # keep relevant columns
    keep_cols = ['year', 'state', 'chamber', 'district', 'candidate',
                 'party', 'candidatevotes']
    df = df[keep_cols]
    df = df.sort_values(by=['state', 'district'])

    # Sum candidate votes
    group_cols = ['year', 'state', 'chamber', 'district', 'candidate', 'party']
    df = df.groupby(group_cols).sum()

    # Reset index and get top candidate for each party
    df = df.reset_index()
    df = df.sort_values(by='candidatevotes', ascending=False)
    duplicate_cols = ['year', 'state', 'chamber', 'district', 'party']
    df = df.drop_duplicates(subset=duplicate_cols)

    # Change MN democratic-farmer-labor to democrat
    df.loc[(df['party'] == 'democratic-farmer-labor') &
           (df['state'] == 'MN'), 'party'] = 'democrat'

    # Rename all other parties as independent
    df['party'] = df['party'].apply(lambda x: x if x in ['democrat',
                                                         'republican']
                                    else 'independent')
    # Pivot the table
    df = pd.pivot_table(df, values='candidatevotes', columns='party',
                        index=['year', 'state', 'chamber', 'district'])
    df = df.fillna(0)
    df = df.reset_index()

    # Get 3 party voteshare
    df['three_sum'] = df['democrat'] + df['independent'] + df['republican']
    df['dem_three'] = df['democrat'] / df['three_sum']
    df['ind_three'] = df['independent'] / df['three_sum']
    df['rep_three'] = df['republican'] / df['three_sum']

    # Get 2 party voteshare
    df['two_sum'] = df['democrat'] + df['republican']
    df['dem_two'] = df['democrat'] / df['two_sum']
    df['rep_two'] = df['republican'] / df['two_sum']
    df = df.drop(columns=['two_sum', 'three_sum'])

    # hardcoded cleaning (HI one-off and UT one-off matching errors)
    df['district'] = df['district'].apply(lambda x: 'District 19'
                                          if x == 'District 19 Vacancy' else x)
    df['district'] = df['district'].apply(lambda x: 'District 8'
                                          if x == 'District 8 (2 year term)'
                                          else x)

    # Get district number for MA
    mass_dict_L, mass_dict_U, _, _ = massachusetts_cleaning()
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
    df = df.append(df_ma_U).append(df_ma_L)
    df['district_num'] = df['district_num'].str.zfill(3)
    return df


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
    df['uncontested'] = df['max_three'] >= 0.8
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


def fundamentals_diff(df_state, df, df_elec):
    """Difference between election outcome and 2018 fundamentals prediction.

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

    # If uncontested let the election be a 35 point swing
    df.loc[(df['uncontested']) & (df['dem_elec'] > 0.5), 'elec_diff'] = 0.35
    df.loc[(df['uncontested']) & (df['dem_elec'] <= 0.5), 'elec_diff'] = -0.35

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


def fundamentals_prediction(df, df_econ, df_diff):
    """Get two party voteshare predictions using fundamentals model.

    Statewide economist forecast + district presidential residual + incumbency
    effect

    Arguments:
        df: lower/upper chamber cleaned moneyball data

        df_econ: current economist forecast

        df_diff: difference between 2018 results and no incumbency fundamentals
                 projected"""
    # Reduce economist data and adjust projected margin to dem voteshare
    df_econ = df_econ[['state', 'margin']]
    df_econ.columns = ['state', 'state_margin']
    df_econ['state_margin'] = df_econ['state_margin'] / 100 + 0.5

    # Join dataframes
    df = df.merge(df_econ).merge(df_diff)

    # Adjust state election difference in direction of incumbent
    df['state_diff'] = df.apply(lambda r: - r['state_diff']
                                if r['incumbent'] == 'R' else r['state_diff'],
                                axis=1)
    df.loc[df['incumbent'].isin(['I', 'False']), 'state_diff'] = 0

    # Calculate incumbency advantage elec_diff
    df['inc_adv'] = df['elec_diff'].fillna(df['state_diff'])

    # Calculate projected district margin w/o incumbency
    df['fund_margin'] = df['state_margin'] + df['resid']

    # Add incumbency advantage
    df['is_inc'] = df['incumbent'].apply(lambda x: 1 if x in ['D', 'R'] else 0)
    df['fund_margin'] += (df['is_inc'] * df['inc_adv'])

    # Clip margin between 0.2 and 0.8
    df['fund_margin'] = np.clip(df['fund_margin'], 0.2, 0.8)

    # Determine if we have results from a past election
    df['past_election'] = df['elec_diff'].notna()

    # Reduce to geoid and fundamentals margin
    df = df[['geoid', 'past_election', 'elec_18', 'fund_margin']]
    return df


if __name__ == "__main__":
    main()
