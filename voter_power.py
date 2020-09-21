# -*- coding: utf-8 -*-
"""
Created on Thu Jun 11 14:04:26 2020
@author: Jacob
"""
import scipy.stats as sts
import numpy as np
import pandas as pd
import itertools as it


def prob_from_margin(margin, race_sigma, race_deg_f, tcdf):
    ''' Given the expected margin of a race and the parameters determining the
    t-distribution about this margin, returns the probability of victory.
    Arguments:
        margin: real number between -1 and 1, expected win margin for candidate
            (negative = loss margin)
        race_sigma: positive real number, estimate of standard deviation of
            actual win margin
        race_df: positive integer, degrees of freedom used in t-distribution
    Output: real number between 0 and 1, probability of candidate winning
    '''
    
    try:
        x = margin/race_sigma
        ix = (x+50)/100 * (len(tcdf)-1)
        floor_ix = int(np.floor(ix))
        frac_ix = ix - floor_ix
        return (1 - frac_ix) * tcdf[floor_ix] + frac_ix * tcdf[floor_ix + 1]
    except:
        print('here')
        return sts.t.cdf(margin / race_sigma, race_deg_f)


def dem_chamber_power(margins, threshold, tie, race_sigma, race_deg_f, tcdf):
    ''' Given a list of expected win margins and the number of seats needed
    for Dem party to have redistricting power, find the probability
    of the Dem party reaching that threshold. Relies on prob_from_margin
    and assumes independence of races.
    Arguments:
        margins: numpy array of expected win margins (between -1 and 1) for
            party (negative = loss margin)
        threshold: number of seats needed for D redistricting power
        tie: probability of D power if they hit "threshold" on the mark
        race_sigma: positive real number, estimate of standard deviation of
            actual win margin in each race
        race_deg_f: positive integer, degrees of freedom used in t-distribution
            in each race
    Output: probability that the party reaches the threshold number of seats,
            assuming independence of race outcomes
    '''

    # find probability of victory for each race
    probs = [prob_from_margin(i, race_sigma, race_deg_f, tcdf) for i in margins]

    # Find full probability distribution of seats won, assuming independence

    # associate with each race a polynomial of the form lose_prob + win_prob*x
    polys = [np.asarray([1 - p, p]) for p in probs]

    # multiply all of these polynomials; the resulting coefficient of x^n
    # is the nth element of the list (index starting at 0), and is the
    # probability of winning exactly n seats
    seat_probs = np.asarray([1])
    for poly in polys:
        seat_probs = np.convolve(seat_probs, poly)

    # return the probability of D redistricting power
    assert threshold < len(seat_probs), (threshold, seat_probs)
    return np.sum(seat_probs[threshold:]) - (1-tie)*seat_probs[threshold]


def success_prob_independence(chamber_1_params, chamber_2_params, race_sigma,
                              race_deg_f, both_bad, neither_bad, tcdf):
    ''' Given two lists of expected win margins and thresholds for Dem party to
    have redistricting power, find the probability of a "good" outcome (no
    single party control). Relies on dem_chamber_power and assumes independence
    of races.
    Arguments:
        chamber_1_params, chamber_2_params: two 3-element lists of the form
            (margins, threshold, tie) to be used by dem_chamber_power
            (see descriptions for each in documentation of dem_chamber_power)
        race_sigma: positive real number, estimate of standard deviation of
            actual win margin in each race
        race_deg_f: positive integer, degrees of freedom used in t-distribution
            in each race
        both_bad: Boolean, is it bad if dems win both chambers? (This happens
            if there is a D governor or governors have no veto power.)'''

    # initialize two-element array of dem control prob of each chamber
    dem_probs = []
    for params in [chamber_1_params, chamber_2_params]:
        margins = list(params[0])
        threshold = params[1]
        tie = params[2]

        # if we are passed 'D' or 'R' in the threshold, this is code that
        # the district is not in question and win probability is fixed
        if threshold == 'D':
            dem_probs.append(1)
        elif threshold == 'R':
            dem_probs.append(0)

        else:
            # find dem chamber power probability and append to win_probs
            p = dem_chamber_power(margins, threshold, tie, race_sigma,
                                  race_deg_f, tcdf)
            dem_probs.append(p)

    # find the probability that we have a good outcome
    good_outcome = 1
    if both_bad:
        good_outcome -= np.prod(dem_probs)
    if neither_bad:
        good_outcome -= (1 - np.sum(dem_probs) + np.prod(dem_probs))

    return good_outcome


def chamber_success_prob(parameter_weights, t_dist_params, threshold_1,
                         threshold_2, tie_1, tie_2, chamber_2_ix,
                         race_sigma, race_deg_f, both_bad, neither_bad, tcdf):
    ''' Finds the probability of chamber success (redistricting power) for a
    state, accounting for various sources of correlated error

    Arguments:
        parameter_weights: numpy matrix with n+1 columns, where the rows denote
            races, the first column denotes the desired candidate's expected
            win margin, and the remaining columns denote the margin's
            sensitivity to an error in a certain parameter
        t_dist_params: list of (sigma, deg_f) for the t-distributed
            random variables, index i corresponds to column i+1 in
            parameter_weights
        threshold_1: number of seats needed for Dem power in chamber 1
            ('D' is code for guaranteed Dem victory, 'R' for Rep victory)
        threshold_2: number of seats needed for Dem power in chamber 2
            ('D' is code for guaranteed Dem victory, 'R' for Rep victory)
        tie_1: estimated probability of D power in chamber 1 if they hit
            "threshold" on the mark
        tie_2: estimated probability of D power in chamber 2 if they hit
            "threshold" on the mark
        chamber_2_ix: row index of parameter_weights where chamber 2 races
            begin (all earlier indices are chamber 1)
        race_sigma: positive real number, estimate of standard deviation of
            actual win margin in each race, after correlated error
        race_deg_f: positive integer, degrees of freedom used in t-distribution
            in each race
        both_bad: Boolean, is it bad if Dems reach threshold in both chambers?
            (This happens if there is a D governor or governors have no
            veto power.)
        neither_bad: Boolean, is it bad if Dems reach threshold in no chamber?
            (This happens if there is a R governor or governors have no
            veto power.)
    '''

    # make sure at least one source of correlated error
    n = len(t_dist_params)
    assert n > 0, "no correlated error encoded"

    # extract sigmas and deg_fs from t_dist_params
    sigmas = [param[0][0] for param in t_dist_params]
    deg_fs = [param[0][1] for param in t_dist_params]
    num_nodes_list = [param[1] for param in t_dist_params]

    # chose sampling points to estimate integration, Chebyshev nodes of
    # percentile function on each distribution
    sample_points = []
    weights = []
    for ix, sig in enumerate(sigmas):

        # get percentiles of nodes
        num_nodes = num_nodes_list[ix]
        nodes = 2*np.linspace(1, num_nodes, num_nodes) - 1
        nodes = np.cos(nodes * np.pi / (2 * num_nodes))
        nodes = (1 + nodes)/2

        # get points, append to list, and get distribution pdfs to
        # weight all points
        points_to_add = sts.t.ppf(nodes, deg_fs[ix], scale=sig)
        sample_points.append(points_to_add)
        weights.append(sts.t.pdf(points_to_add, deg_fs[ix], scale=sig))

    # cartesian product to get all correlated errors at once, relative weights
    all_shifts = list(it.product(*sample_points))
    all_shifts = [list(i) for i in all_shifts]
    all_weights = [np.prod(i) for i in list(it.product(*weights))]
    total_weight = np.sum(all_weights)

    success_weight = 0
    for ix, shift_vector in enumerate(all_shifts):

        # find expected margins before independent race shift
        # append 1 at the beginning to add in the starting margin
        margins = parameter_weights.dot(np.asarray([1] + shift_vector))

        # generate list of parameters for the two chambers
        params_1 = [margins[:chamber_2_ix], threshold_1, tie_1]
        params_2 = [margins[chamber_2_ix:], threshold_2, tie_2]

        # find success_prob
        success = success_prob_independence(params_1, params_2, race_sigma,
                                            race_deg_f, both_bad, neither_bad,
                                            tcdf)

        # add to weighted success probability
        success_weight += all_weights[ix] * success

    return success_weight / total_weight


def voter_power(districts_df, error_vars, race_sigma, race_deg_f, both_bad,
                neither_bad, margin_col, voters_col, threshold_col, tie_col,
                chamber_col, power_col, prob_only, tcdf):
    ''' Finds the power of one vote in each district (i.e. the increase in
    probability that the party reaches the necessary number of seats if they
    gain one extra vote)

    Arguments:
        districts_df: pandas DataFrame of districts, indexed by 0, 1, 2, ..
            with (at least) these columns:
            margin_col: the expected winning margin for the party (negative if
                    losing margin)
            voters_col: the number of voters in the district
            threshold_col: threshold for Dem power in redistricting process
            tie_col: estimated probability of Dem power if they hit the
                threshold on the mark
            chamber_col: the district's chamber
        error_vars: dictionary where keys are the columns in districts_df that
            are sources of error, values are (sigma, deg_f) of t-distribution
            of the error and number of nodes for numerical integration accuracy
                format: (sigma, deg_f), nodes
        threshold: number of seats needed for redistricting power
        race_sigma: positive real number, estimate of standard deviation of
            actual win margin in each race, after correlated error
        race_deg_f: positive integer, degrees of freedom used in t-distribution
            in each race
        both_bad: Boolean, is it bad if Dems reach threshold in both chambers?
            (This happens if there is a D governor or governors have no
            veto power.)
        neither_bad: Boolean, is it bad if Dems reach threshold in no chamber?
            (This happens if there is a R governor or governors have no
            veto power.)
    Output: input DataFrame with one column added, power_col, which
            gives the result of the calculation for each district'''

    # generate parameter_weights
    parameter_weights = districts_df[error_vars].to_numpy()

    # append margins to the first column of parameter_weights
    margins = districts_df[margin_col].to_numpy()
    margins.shape = (len(districts_df), 1)
    parameter_weights = np.hstack((margins, parameter_weights))

    # get total_votes by district
    votes_by_district = list(districts_df[voters_col])

    # extract sigmas, deg_fs from error_vars
    t_dist_params = list(error_vars.values())

    # find the first index of chamber 2 in margins and (parameter_weights)
    chambers = list(districts_df[chamber_col])
    chamber_2_ix = chambers.index(chambers[-1])

    # find thresholds and ties
    thresholds = list(districts_df[threshold_col])
    threshold_1 = int(thresholds[0])
    threshold_2 = int(thresholds[-1])

    ties = list(districts_df[tie_col])
    tie_1 = ties[0]
    tie_2 = ties[-1]

    # check if the race is already won in a chamber ##

    # initialize some variables
    test_cham_1 = True
    test_cham_2 = True

    # find number of competitive seats per chamber
    possible_seats_1 = chamber_2_ix
    possible_seats_2 = len(margins) - possible_seats_1

    # if D's already won chamber 1
    if threshold_1 <= 0:
        test_cham_1 = False
        threshold_1 = 'D'

    # if R's already won chamber 1
    elif threshold_1 > possible_seats_1:
        test_cham_1 = False
        threshold_1 = 'R'

    # if D's already won chamber 2
    if threshold_2 <= 0:
        test_cham_2 = False
        threshold_2 = 'D'

    # if R's already won chamber 1
    elif threshold_2 > possible_seats_2:
        test_cham_2 = False
        threshold_2 = 'R'

    # find the chamber success probability
    prob = chamber_success_prob(parameter_weights, t_dist_params, threshold_1,
                                threshold_2, tie_1, tie_2, chamber_2_ix,
                                race_sigma, race_deg_f, both_bad, neither_bad,
                                tcdf)

    # if we just cared about election results
    if prob_only:
        return prob

    # initialize dictionary keyed by parameter weights, where the value is
    # voter_power * voters_in_district, which is very nearly constant for
    # each set of weights, assuming locally linear behavior, which is observed
    # to cause < 0.1% error
    voter_power_dict = {}

    # intitialize voter_powers list
    voter_powers = []

    # for all races
    for i in range(len(parameter_weights[:, 0])):
        # make sure the chamber is in doubt, if not assign voter power 0
        if i < chamber_2_ix:
            if not test_cham_1:
                voter_powers.append(0)
                continue
        else:
            if not test_cham_2:
                voter_powers.append(0)
                continue

        # grab the number of voters in the district of interest
        num_voters = votes_by_district[i]

        # grab relevant parameter weights for this race
        race_weights = list(parameter_weights[i, :])

        # grab chamber identifier
        chamber_bool = i < chamber_2_ix

        # together, the chamber and set of weights and give voter power
        # almost exactly inverse proportional to voters
        unique_params = tuple(race_weights + [chamber_bool])

        # if we have not already done a race with these exact weights
        # in this chamber
        if unique_params not in voter_power_dict:

            # deep copy parameter_weights
            param_weights_copy = parameter_weights.copy()

            # adjust the margin in our race, assuming the party gained 1 vote
            param_weights_copy[i, 0] += 1 / num_voters

            # find the chamber success probability
            prob_new = chamber_success_prob(param_weights_copy, t_dist_params,
                                            threshold_1, threshold_2, tie_1,
                                            tie_2, chamber_2_ix, race_sigma,
                                            race_deg_f, both_bad, neither_bad, 
                                            tcdf)

            # update dictionary with quantity voter_power * voters_in_district
            voter_power_dict[unique_params] = (prob_new - prob) * num_voters

        # calcuate vote power, to later add to proper column of districts_df
        voter_powers.append(voter_power_dict[unique_params] / num_voters)

    # add voter power column and return
    districts_df[power_col] = voter_powers
    return districts_df


def rating_to_margin(favored, confidence, df):
    ''' Gets the expected margin of victory based on information in
    two input parameter files.

    Arguments:
        favored: 'D', 'R', 'I', or FALSE (in case of Toss-Up)
        confidence: 'Toss-Up', 'Tilt', 'Lean', 'Likely', or 'Uncontested'
        df: pandas DataFrame with two columns, 'RATING' and 'MARGIN' that give
            expected margin of victory associated with each rating


    Output: expected margin of victory, positive if Dem, negative if Rep'''

    # get absolute margin
    margin = df.loc[confidence, 'MARGIN']

    # positive if dem, negative if rep, None if ind
    if favored == 'R':
        margin = -margin
    if favored == 'I':
        raise ValueError('You must handle independents manually and remove')

    return margin


def state_voter_powers(all_races, margin_col, voters_col, threshold_col,
                       tie_col, chamber_col, power_col, state, error_vars,
                       race_sigma, race_deg_f, rating_to_margin_df, tcdf,
                       found_margin_col=False, found_clip=False,
                       blend_safe=False, blend_else=False, prob_only=False):
    ''' Gets all voter powers in a state.

    Arguments:
        all_races: DataFrame with all races, generated by
            cnalysis_input_components.py with (at least) these columns:

            margin_col: the expected winning margin for the party (negative if
                    losing margin)
            voters_col: the number of voters in the district
            threshold_col: threshold for Dem power in redistricting process
            tie_col: estimated probability of Dem power if they hit the
                threshold on the mark
            chamber_col: the district's chamber
            found_margin_col (optional): the expected winning margin based
                on a foundational model, to blend with margin_col. Note: if
                this column is passed, must also pass:
                    found_clip: clip found_margin at certain distance from
                        margin to avoid adjusting too aggressively when the
                        forecaster has knowledge we do not
                    blend_safe: what fraction of foundational margin to use
                        in weighted average with margin in *safe* seats
                        (spilitting this category since "safe" is a much
                        wider range of outcomes than others)
                    blend_else: what fraction of foundational margin to use
                        in weighted average with margin in non-safe seats

        state: postal code of state to find voter powers
        error_vars: dictionary where keys are the columns in districts_df that
            are sources of error, values are (sigma, deg_f) of t-distribution
            of the error and number of nodes for numerical integration accuracy
                format: (sigma, deg_f), nodes
        race_sigma: positive real number, estimate of standard deviation of
            actual win margin in each race, after correlated error
        race_deg_f: positive integer, degrees of freedom used in t-distribution
            in each race
        rating_to_margin_df: pandas DataFrame with two columns, 'RATING' and
            'MARGIN' that give expected margin of victory associated with each
            rating
        prob_only (optional): cuts function off early and just returns the
            probability of bipartisan control

    Output: DataFrame of races in this state with voter power column added
    '''
    # restrict dataframe to this state
    st_races = all_races[all_races['state'] == state].copy()

    # find number of uncontested Dem seats in each chamber
    d_uncont = {'lower': False, 'upper': False}
    for chamber in d_uncont:
        cham_df = st_races[st_races['office'] == chamber]
        d_uncont[chamber] = sum(cham_df.apply(lambda x: x['favored'] == 'D' and
                                              x['confidence'] == 'Uncontested',
                                              axis=1))

    # remove uncontested seats and update thresholds
    st_races = st_races[st_races['confidence'] != 'Uncontested']
    st_races[threshold_col] = st_races.apply(lambda x: x[threshold_col] -
                                             d_uncont[x['office']], axis=1)

    # remove safe and uncontested independents, lower threshold by 1 and
    # cut tie prob in half (roughly, this assumes indies break to either
    # party with equal probability in a redistricting coalition)
    indies = st_races[(st_races['favored'] == 'I') &
                      (st_races['confidence'].isin(['Safe', 'Uncontested']))]
    for ix, row in indies.iterrows():
        st_races[threshold_col] -= 1
        st_races[tie_col] /= 0.5
        st_races = st_races.drop(ix)

    # add margin column
    st_races[margin_col] = st_races.apply(lambda x:
                                          rating_to_margin(x.favored,
                                                           x.confidence,
                                                           rating_to_margin_df),
                                          axis=1)

    # adjust margin column based on foundational model
    if found_margin_col:

        """MAKE NAMES SHORTER AND CLEAN UP STYLING"""
        # clip margins if needed
        if found_clip:
            st_races['unclipped_' + found_margin_col] = \
                                        st_races[found_margin_col]
            st_races[found_margin_col] = st_races.apply(lambda x: \
                        min(x[found_margin_col], x[margin_col] + found_clip),\
                        axis=1)
            st_races[found_margin_col] = st_races.apply(lambda x: \
                        max(x[found_margin_col], x[margin_col] - found_clip),\
                        axis=1)

        # blend margins
        st_races['orig_' + margin_col] = st_races[margin_col]
        st_races[margin_col] = st_races.apply(lambda x: blend_safe * \
                    x[found_margin_col] + (1 - blend_safe) * x[margin_col] \
                    if x['confidence'] == 'Safe' else blend_else * \
                    x[found_margin_col] + (1 - blend_else) * x[margin_col],\
                    axis=1)

    # determine if it is bad for dems to win both
    both_bad = st_races['both_bad'].unique()[0]

    # determine if it is bad for dems to win neither
    neither_bad = st_races['neither_bad'].unique()[0]

    # calculate voter power, add column to df
    st_races = voter_power(st_races, error_vars, race_sigma, race_deg_f,
                           both_bad, neither_bad, margin_col, voters_col,
                           threshold_col, tie_col, chamber_col, power_col,
                           prob_only, tcdf)
    return st_races
