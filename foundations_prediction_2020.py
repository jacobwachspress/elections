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
    df_economist = pd.read_csv(economist_path)

    # Get cleaned moneyball data
    df_lower = pd.read_csv(money_path + 'state/lower_input_data.csv')
    df_upper = pd.read_csv(money_path + 'state/upper_input_data.csv')

    # Format district number and drop unnecessary columns
    df_lower = clean_incumbency(df_lower)
    df_upper = clean_incumbency(df_upper)
    d_num = 'district_num'
    df_lower[d_num] = df_lower[d_num].astype(str).str.zfill(3)
    df_upper[d_num] = df_upper[d_num].astype(str).str.zfill(3)
    keep_cols = ['state', 'district_num', 'incumbent_18', '2016_win_margin',
                 '2016_win_party']
    df_lower = df_lower[keep_cols]
    df_upper = df_upper[keep_cols]

    # Load election results and incumbency results
    df_elec = pd.read_csv(money_path + 'elections/election_results_2018.csv')
    df_inc_lower = pd.read_csv(path +
                               'clean/lower_chamber_incumbency_2016_2020.csv')
    df_inc_upper = pd.read_csv(path +
                               'clean/upper_chamber_incumbency_2016_2020.csv')

    # Load district based residuals
    df_lower_resid = pd.read_csv(path + 'clean/imputed_sldl_residuals.csv')
    df_upper_resid = pd.read_csv(path + 'clean/imputed_sldu_residuals.csv')

    # Compile historical results
    df = compile_historical_results(df_elec, df_lower, df_upper, df_inc_lower,
                                    df_inc_upper)

    # Add 2016 election results
    df = add_national_results(df, df_state, df_lower_resid, df_upper_resid)

    # Calculate incumbency advantage
    df = incumbency_advantage(df)

    # Calculate foundations prediction
    df = foundation_prediction(df, df_economist)
    df.to_csv(path + 'clean/foundations_predictions_2020.csv', index=False)
    return


def compile_historical_results(df, df_lower, df_upper, df_inc_lower,
                               df_inc_upper):
    """Compile 2018 and 2016 election results.

    Arguments:
        df: 2018 election data

        df_lower: lower chamber input data

        df_upper: upper chamber input data

        df_inc_lower: 2016 and 2020 incumbency data

        df_inc_upper: 2016 and 2020 incumbendy data
    """
    # Get district number as zfilled to 3
    df['district_num'] = df['district_num'].astype(str).str.zfill(3)
    d_num = 'district_num'
    df_inc_lower[d_num] = df_inc_lower[d_num].astype(str).str.zfill(3)
    df_inc_upper[d_num] = df_inc_upper[d_num].astype(str).str.zfill(3)

    # Simplify vote count names
    df['D'] = df['democrat']
    df['R'] = df['republican']
    df['I'] = df['independent']
    drop_cols = ['democrat', 'republican', 'independent', 'year', 'dem_two',
                 'rep_two', 'district', 'dem_cand', 'ind_cand', 'rep_cand']
    df = df.drop(columns=drop_cols)

    # Fix the tie in Alaska
    df.loc[(df['state'] == 'AK') & (df['district_num'] == '001'), 'R'] += 1

    # Get the winning party
    df['win_party'] = df[['D', 'R', 'I']].idxmax(axis=1)

    # Check if the race was essentially uncontested
    df['max_three'] = df[['dem_three', 'rep_three', 'ind_three']].max(axis=1)
    df['uncontested'] = df['max_three'] >= 0.75

    # Drop unncessary columns
    drop_cols = ['max_three', 'dem_three', 'ind_three', 'rep_three']
    df = df.drop(columns=drop_cols)

    # Get the party that got the least votes
    df['worst_party'] = df[['D', 'R', 'I']].idxmin(axis=1)

    # Impute independent as other party if other party has no candidate
    df['D'] = df.apply(lambda r: r['I'] if ((r['win_party'] == 'R') &
                                            (r['D'] == 0)) else r['D'], axis=1)
    df['R'] = df.apply(lambda r: r['I'] if ((r['win_party'] == 'D') &
                                            (r['R'] == 0)) else r['R'], axis=1)

    # Convert to margin and then to two party voteshare
    df['dem_elec'] = df['D'] / (df['D'] + df['R'])

    # Split into lower and upper
    df_elec_lower = df[df['chamber'] == 'lower']
    df_elec_upper = df[df['chamber'] == 'upper']

    # Drop relevant columns
    drop_cols = ['D', 'R', 'I', 'worst_party', 'chamber']
    df_elec_lower = df_elec_lower.drop(columns=drop_cols)
    df_elec_upper = df_elec_upper.drop(columns=drop_cols)

    # Rename columns
    new_cols = ['state', 'district_num', 'win_party_18', 'uncontested_18',
                'dem_share_18']
    df_elec_lower.columns = new_cols
    df_elec_upper.columns = new_cols

    # Join to input data
    df_lower = df_lower.merge(df_elec_lower, on=['state', 'district_num'],
                              how='left')
    df_upper = df_upper.merge(df_elec_upper, on=['state', 'district_num'],
                              how='left')

    # Clean data if incumbent won election in 2016
    df_inc_lower['incumbent_16'] = df_inc_lower['incumbent']
    df_inc_upper['incumbent_16'] = df_inc_upper['incumbent']
    keep_cols = ['state', 'district_num', 'incumbent_16']
    df_inc_lower = df_inc_lower[keep_cols]
    df_inc_upper = df_inc_upper[keep_cols]

    # Join incumbency data
    df_lower = df_lower.merge(df_inc_lower, on=['state', 'district_num'],
                              how='left')
    df_upper = df_upper.merge(df_inc_upper, on=['state', 'district_num'],
                              how='left')

    # winning party in 2016
    df_lower['win_party_16'] = df_lower['2016_win_party']
    df_upper['win_party_16'] = df_upper['2016_win_party']

    # Get dem vote share 2018
    df_lower.loc[df_lower['win_party_16'] == 'R',
                 '2016_win_margin'] *= -1
    df_lower['dem_share_16'] = df_lower['2016_win_margin'] / 2 + 0.5
    df_upper['dem_share_16'] = df_upper['2016_win_margin'] / 2 + 0.5

    # Get if race was effectively uncontested
    df_lower['uncontested_16'] = df_lower['dem_share_16'] - 0.5
    df_lower['uncontested_16'] = np.abs(df_lower['uncontested_16']) > 0.25
    df_upper['uncontested_16'] = df_upper['dem_share_16'] - 0.5
    df_upper['uncontested_16'] = np.abs(df_upper['uncontested_16']) > 0.25

    # Drop unnecessary columns
    drop_cols = ['2016_win_margin', '2016_win_party']
    df_lower = df_lower.drop(columns=drop_cols)
    df_upper = df_upper.drop(columns=drop_cols)

    # Compile into one dataframe
    df_lower['chamber'] = 'lower'
    df_upper['chamber'] = 'upper'
    df = df_lower.append(df_upper)
    return df


def add_national_results(df, df_state, df_lower, df_upper):
    """Add 2016 election results for each state legislative district.

    Arguments:
        df: historical state legislative election results

        df_state: statewide presidential election results

        df_lower_resid: lower chamber residuals for national election

        df_upper_resid: upper chamber residuals for national election
    """
    # Clean and merge state presidential data
    df_state = df_state.drop(columns=['dem_12', 'rep_12', 'rep_16'])
    df_state.columns = ['state', 'dem_state']
    df = df.merge(df_state)

    # Clean residual data. add chamber type
    df_lower['chamber'] = 'lower'
    df_upper['chamber'] = 'upper'

    # Reduce columns
    keep_cols = ['state', 'district_num', 'resid', 'chamber']
    df_lower = df_lower[keep_cols]
    df_upper = df_upper[keep_cols]

    # Create as one dataframe
    df_resid = df_lower.append(df_upper)
    df_resid['district_resid'] = df_resid['resid']
    df_resid = df_resid.drop('resid', axis=1)
    df_resid['district_num'] = df_resid['district_num'].astype(str)
    df_resid['district_num'] = df_resid['district_num'].str.zfill(3)

    # Join residuals to election data
    df = df.merge(df_resid, on=['state', 'district_num', 'chamber'],
                  how='left')

    # Calculate the district presidential dem voteshare
    df['dem_pres_16'] = df['dem_state'] + df['district_resid']
    return df


def incumbency_advantage(df):
    """Add average incumbency advantage over the past two years."""
    # Get the election difference for each year
    df['elec_diff_18'] = df['dem_share_18'] - df['dem_pres_16']
    df['elec_diff_16'] = df['dem_share_16'] - df['dem_pres_16']

    # If uncontested, let the election difference be a 20 point swing
    df.loc[(df['uncontested_18']) &
           (df['dem_share_18'] > 0.5), 'elec_diff_18'] = 0.2
    df.loc[(df['uncontested_18']) &
           (df['dem_share_18'] <= 0.5), 'elec_diff_18'] = -0.2
    df.loc[(df['uncontested_16']) &
           (df['dem_share_16'] > 0.5), 'elec_diff_16'] = 0.2
    df.loc[(df['uncontested_16']) &
           (df['dem_share_16'] <= 0.5), 'elec_diff_16'] = -0.2

    # Get the observed incumbency advantage
    df.loc[df['incumbent_16'].isin(['D', 'R']),
           'obs_inc_16'] = df['elec_diff_16']
    df.loc[df['incumbent_18'].isin(['D', 'R']),
           'obs_inc_18'] = df['elec_diff_18']

    # Get the average incumbency advantage between the two years
    df['inc_adv'] = np.mean(df[['obs_inc_16', 'obs_inc_18']],
                            axis=1).fillna(0)
    df['inc_adv'] = np.clip(df['inc_adv'], -0.2, 0.2)
    return df


def clean_incumbency(df):
    """Clean incumbency data in a dataframe.

    If party is favored and nominee is TBA then assume its
    and incumbent. Do the same if nominee is False.

    Keep like this because primaries are not finished
    """
    df.loc[(df['favored'] == 'D') &
           (df['nom_D'] == 'TBA'), 'incumbent'] = 'D'
    df.loc[(df['favored'] == 'D') &
           (df['nom_D'].astype(str) == 'False'), 'incumbent'] = 'D'
    df.loc[(df['favored'] == 'R') &
           (df['nom_R'] == 'TBA'), 'incumbent'] = 'R'
    df.loc[(df['favored'] == 'R') &
           (df['nom_R'].astype(str) == 'False'), 'incumbent'] = 'R'
    df['incumbent_18'] = df['incumbent']
    return df


def foundation_prediction(df, df_econ):
    """Get final foundations prediction."""
    # Clean economist margins
    df_econ = df_econ[['state', 'margin']]
    df_econ.columns = ['state', 'state_margin']
    df_econ['dem_pres_20'] = df_econ['state_margin'] / 200 + 0.5
    df_econ = df_econ.drop('state_margin', axis=1)

    # Join dataframes
    df = df.merge(df_econ)

    # Let the nationwide vote share estimate be the average of economist
    # prediction and 2016
    df['dem_pres'] = 0.5 * df['dem_pres_16'] + 0.5 * df['dem_pres_20']

    # HAND FIX INCUMBENCY ADVANTAGE DATA ERRORS

    # Dinah Sikes in KS changed parties
    df.loc[(df['state'] == 'KS') & (df['district_num'] == '008')
           & (df['chamber'] == 'upper'), 'inc_adv'] = 0.078

    # Julia Lynn has the wrong dem_share_16
    df.loc[(df['state'] == 'KS') & (df['district_num'] == '008')
           & (df['chamber'] == 'upper'), 'inc_adv'] = 0.02

    # Get the foundational voteshare and margin
    df['found_share'] = df['dem_pres'] + df['inc_adv']
    df['found_share'] = np.clip(df['found_share'], 0.3, 0.7)
    df['found_margin'] = (df['found_share'] - 0.5) * 2
    return df


if __name__ == "__main__":
    main()
