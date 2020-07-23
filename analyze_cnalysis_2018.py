# -*- coding: utf-8 -*-
"""
Created on Tue Jul  7 15:29:39 2020

@author: Jacob
"""
import pandas as pd
import numpy as np
import scipy.stats as sts
import scipy.linalg as lin


def main():

    # set google drive path for files
    money_path = 'G:\\Shared drives\\princeton_gerrymandering_project\\Moneyball\\'

    # read in results
    results_df = pd.read_csv(money_path +\
                             'chaz\\chaz_with_election_results.csv')
    
    sts_df = generate_summary_stats(results_df)

    results_df = add_overperformance(results_df, sts_df)
    
    results_temp = add_overperformance(results_df, sts_df)

    results_temp = get_density_proportions(results_temp)
def t_parameter_tester(margin, params_list, delta=10000):
    ''' Estimates win probability given expected win margin and list of
    t-distributions of independent errors.

    Arguments:
        margin: expected win margin, from -1 to 1
        params_list: list of pairs (sigma, degrees of freedom) representing the
            parameters for the independent t-distributed random variables to be
            added to the expected win margin to get the result
        delta: resolution for estimating integral

    Output: win probability'''

    ## discretize space, convolve a whole bunch of distributions ##

    # initialize distribution
    convolved = np.asarray([1])

    # for each pair of t-distribution parameters
    for sigma, deg_f in params_list:

        # discretize the region [-1, 1] in delta parts
        discretized_space = np.linspace(-1, 1, delta+1)

        # find the discretized PDF of the t-distribution given these params
        pdf = np.ravel(sts.t.pdf(discretized_space / sigma, deg_f))

        # convolve this distribution into convolved
        convolved = np.convolve(convolved, pdf)

    # set convolved sum to 1, so it is a pdf
    convolved = convolved/sum(convolved)

    ## find cdf at given margin ##

    # find endpoints of intervals of convolved pdf [-endpt, endpt]
    endpt = len(params_list)

    # find total number of pieces into which the interval is carved
    pieces = endpt * delta

    # find relative position of margin among the pieces in this interval
    pos = pieces * (margin + endpt) / (2*endpt)

    # split pos into integer and fracitonal parts
    ix = int(np.floor(pos))
    frac = pos - ix

    # estimate cdf by adding pdf up to this index, principled linear guess
    # for the error due to not being right on an index
    return sum(convolved[:ix]) + frac * convolved[ix]

def generate_summary_stats(results_df):

    # filter oddball seats
    results = results_df[results_df['ignore'] != True]

    # get the states and confidence levels
    states = results['state_po'].dropna().unique()
    confidences = results['confidence'].dropna().unique()

    # initialize a dataframe for statewide and national analysis
    sts_df = pd.DataFrame({'STATE' : list(states) + ['USA']}).set_index('STATE')

    # for each state
    for state, _ in sts_df.iterrows():

        # splice results DataFrame to get all results from this state
        if state != 'USA':
            state_df = results[results['state_po'] == state]
        else:
            state_df = results

        # for each confidence
        for conf in confidences:

            # splice df to only this confidence
            df = state_df[state_df['confidence'] == conf].copy()

            # find all outliers (probably surprise uncontesteds)
            outliers_df = df[df['win_margin'] > 0.9]
            sts_df.loc[state, conf + '_was_uncontested'] = len(outliers_df)

            # find all outlier misses
            lost_uncontest = outliers_df[outliers_df['correct'] == False]
            sts_df.loc[state, conf + '_lost_uncontested'] = len(lost_uncontest)

            # delete outliers
            df = df[df['win_margin'] <= 0.9]

            # find count of races in this category
            sts_df.loc[state, conf + '_count'] = len(df)

            # find count of races in this category
            sts_df.loc[state, conf + '_correct'] = \
                                            len(df[df['correct'] == True])

            # find mean winning margin
            sts_df.loc[state, conf + '_mean_win_margin'] = \
                                            df['actual_win_margin'].mean()

            # find variance of winning margin
            sts_df.loc[state, conf + '_variance_win_margin'] = \
                                    df['actual_win_margin'].var()

            # if there are races
            if len(df) > 0:
                # fit t-distribution
                deg_f, mean, sigma = sts.t.fit(df['actual_win_margin'])

                # save these
                sts_df.loc[state, conf + '_t_mean'] = mean
                sts_df.loc[state, conf + '_t_sigma'] = sigma
                sts_df.loc[state, conf + '_t_deg_f'] = deg_f

        conf = 'ALL'
        df = state_df.copy()

        # find all outliers (probably surprise uncontesteds)
        outliers_df = df[df['win_margin'] > 0.9]
        sts_df.loc[state, conf + '_was_uncontested'] = len(outliers_df)

        # find all outlier misses
        outlier_losers_df = outliers_df[outliers_df['correct'] == False]
        sts_df.loc[state, conf + '_lost_uncontested'] = len(outlier_losers_df)

        # delete outliers
        df = df[df['win_margin'] <= 0.9]

        # find count of races in this category
        sts_df.loc[state, conf + '_count'] = len(df)

        # find count of races in this category
        sts_df.loc[state, conf + '_correct'] = len(df[df['correct'] == True])

        # find mean winning margin
        sts_df.loc[state, conf + '_mean_win_margin'] = \
                                        df['actual_win_margin'].mean()

        # find variance of winning margin
        sts_df.loc[state, conf + '_variance_win_margin'] = \
                                df['actual_win_margin'].var()

    return sts_df

def get_margins(st_stats, confidences=['Tilt', 'Lean', 'Likely', 'Safe']):
    ''' Expected win margin by category, based on 2018 data'''

    # build dictionary of expected win margin by confidence
    expected_win_margins = {}
    for conf in confidences:
        expected_win_margins[conf] = st_stats.loc['USA', conf + '_t_mean']
        
    return expected_win_margins

def add_overperformance(results_df, st_stats):

    # filter oddball seats
    results = results_df[results_df['ignore'] != True]
    
    # remove safe seats (uncontested issues)
    results = results[results['confidence'] != 'Safe']

    # remove predicted I winners
    results = results[results['predicted_winner'] != 'I']

    expected_win_margins = get_margins(results, st_stats)

    # add expected win margin column to results DataFrame
    results['expected_win_margin'] = results['confidence'].apply(lambda x: \
           expected_win_margins[x])

    # add R overperformance column
    results['R_overperformance'] = results.apply(lambda x: \
        x['actual_win_margin'] - x['expected_win_margin'] if \
        x['predicted_winner'] == 'R' else x['expected_win_margin'] - \
        x['actual_win_margin'] if x['predicted_winner'] == 'D' else 0, axis=1)

    # find average R_overperformance by state, add column to isolate race effects



    # dictionary of mean R_overperformance
    R_dict = results.groupby(['state_po'])['R_overperformance'].mean().to_dict()

    # add column with these numbers
    results['state_R_overperformance'] = results['state_po'].apply(lambda x: \
                                                   R_dict[x])

    # add column with isolated error, in direction of GOP
    results['isolated_race_error'] = results.apply(lambda x: \
           x['R_overperformance'] - x['state_R_overperformance'], axis=1)

    return results

def get_density_proportions(results):
    columns = ['rural', 'exurban', 'suburban', 'urban']
    results['pop'] = results[columns].sum(axis=1)
    for col in columns:
        results[col + '_prop'] = results[col] / results['pop']
    return results

def fit_t(results):
    # fit t-distribution
    deg_f, _, sig = sts.t.fit(results['isolated_race_error'], floc=0)
    st_deg_f, _, st_sig = sts.t.fit(results['state_R_overperformance'], floc=0)

    return deg_f, sig, st_deg_f, st_sig



def simulate(n, results_df, race_sig, race_df):
    
    sim_results = results_df.copy()
    
    corr_cols = ['rural_prop', 'exurban_prop', 'suburban_prop', 'urban_prop']
    corr_dict = {}
    for i in corr_cols:
        corr_dict[i] = []

    for trial in range(n):
        sim_results['R_overperformance'] = race_sig*sts.t.rvs(race_df, \
                                   size=len(sim_results['R_overperformance']))
#        state_errors = {}
#        for i in states:
#            state_errors[i] = st_sig*sts.t.rvs(st_df)
#        results['R_overperformance'] = results.apply(lambda x: \
#                  x['R_overperformance'] + state_errors[x['state_po']], axis=1)

        # add column with statewide overperformance
        R_dict = sim_results.groupby(['state_po'])['R_overperformance'].mean()\
                                .to_dict()
        sim_results['state_R_overperformance'] = sim_results['state_po']\
                                            .apply(lambda x: R_dict[x])

        # add column with isolated error, in direction of GOP
        sim_results['isolated_race_error'] = sim_results.apply(lambda x: \
            x['R_overperformance'] - x['state_R_overperformance'], axis=1)

        for col in corr_cols:
            corr = np.corrcoef(sim_results['R_overperformance'], \
                               sim_results[col])
            corr_dict[col].append(corr[1,0])
            
    return corr_dict

if __name__ == '__main__':
    main()