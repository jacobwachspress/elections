# -*- coding: utf-8 -*-
"""
Created on Thu Jun 11 14:04:26 2020
@author: Jacob
"""
import scipy
import scipy.stats as sts
from scipy.integrate import quad
import numpy as np
import pandas as pd

# MONEYBALL PATH FOR GOOGLE DRIVE
moneyball_path = 'G:/Shared drives/princeton_gerrymandering_project/Moneyball/'
count = 0

def margins_from_ratings(ratings):
    return


def success_prob_from_meta_margin(meta_margin, meta_sigma=0.03, meta_df=2):
    '''Given the meta-margin for the party reaching the desired threshold and
    the parameters determining the t-distribution about this margin, returns
    the party's probability of reaching this threshold.
    Arguments:
        meta_margin: real number, as calculated by find_meta_margin
        meta_sigma: positive real number, estimate of standard deviation of
            actual meta-margin
        race_df: positive integer, degrees of freedom used in t-distribution
    Output: real number between 0 and 1, probability of party reaching
            threshold
    '''
    return sts.t.cdf(meta_margin / meta_sigma, meta_df)


def success_prob_from_margin(margin, race_sigma=0.07, race_df=2):
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
    return sts.t.cdf(margin / race_sigma, race_df)


def chamber_success_prob_assuming_independence(margins, threshold):
    ''' Given a list of expected win margins and the number of seats needed
    for the party to have desired redistricting power, find the probability
    of the party reaching that threshold. Relies on success_prob_from_margin
    and assumes independence of races.
    Arguments:
        margins: numpy array of expected win margins (between -1 and 1) for
            party (negative = loss margin)
        threshold: number of seats needed for redistricting power
    Output: probability that the party reaches the threshold number of seats,
            assuming independence of race outcomes
    '''

    # find probability of victory for each race
    probs = [success_prob_from_margin(i) for i in margins]

    # # Find full probability distribution of seats won, assuming independence

    # associate with each race a polynomial of the form lose_prob + win_prob*x
    polys = [np.asarray([1 - p, p]) for p in probs]

    # multiply all of these polynomials; the resulting coefficient of x^n
    # is the nth element of the list (index starting at 0), and is the
    # probability of winning exactly n seats
    seat_probs = np.asarray([1])
    for poly in polys:
        seat_probs = np.polymul(seat_probs, poly)

    # return the probability of reaching the threshold
    return np.sum(seat_probs[threshold:])


def find_meta_margin(margins, seats_needed):
    ''' Given a list of expected win margins and the number of seats needed
    for the party to have desired redistricting power, finds the Meta-Margin.
    The Meta-Margin is the margin that all seats would have to shift uniformly
    so that the probability of the party reaching that threshold is
    exactly 0.50, assuming independence of races. (By convention,
    positive Meta-Margin implies the party is favored.)
    The Meta-Margin is unique because the win probability varies monotonically
    with the uniform shift. The idea here is to use bisection to estimate the
    Meta-Margin numerically.
    Arguments:
        margins: numpy array of expected win margins for party
            (negative = loss margin)
        seats_needed: number of seats needed for redistricting power
    Output: Meta-Margin
    '''

    # set bounds for Meta-Margin, initialize accuracy threshold eps
    min_margin = -30
    max_margin = 30
    eps = 1e-15

    # while we still have a range of uncertainty of length at least eps
    while max_margin - min_margin > eps:

        # find the middle of the range, shift all margins by this amount
        # against the party
        average = (min_margin + max_margin) / 2
        adjusted_margins = margins - average

        # find the win probability with these shifted margins
        prob = chamber_success_prob_assuming_independence(adjusted_margins,
                                                          seats_needed)

        # depending on whether this probability is below or above 0.5,
        # modify the search bounds appropriately
        if prob < 0.5:
            max_margin = average
        else:
            min_margin = average

    # return an endpoint of the interval, which has converged to a point
    return min_margin


def chamber_success_prob(margins, threshold):
    ''' Given a list of expected win margins and the number of seats needed
    for the party to have desired redistricting power, find the probability
    of the party reaching that threshold. Uses Meta-Margin technique.
    Arguments:
        margins: numpy array of expected win margins (between -1 and 1) for
            party (negative = loss margin)
        threshold: number of seats needed for redistricting power
    '''

    return success_prob_from_meta_margin(find_meta_margin(margins, threshold))

def chamber_success_prob_with_shift(shift, margins, threshold, \
                                    statewide_sigma = 0.04, statewide_deg_f=2):
    ''' Helper method to be integrated in better_chamber_success_prob.
    Assuming independence of races, calculates the probability of the party
    reaching a fixed threshold of seats after a uniform shift in all margins,
    then multiplies by the probability density function of the statewide shift
    distribution at this point.
    Integrating over all shifts will give the probability of reaching that 
    threshold, assuming uncorrelated error among seats after the statewide
    shift.
    
    Arguments:
        shift: real number between -1 and 1, how much all seats the state are 
            shifted in favor of the party     
        margins: numpy array of expected win margins (between -1 and 1) for 
            party before the statewide shift (negative = loss margin)    
        threshold: number of seats needed for redistricting power    
        statewide_sigma: positive real number, estimate of standard deviation 
            of statewide error    
        statewide_deg_f: positive integer, degrees of freedom used in 
            t-distribution
        
    Output: A * B, where
        A = probability that the party reaches the threshold number of seats,
            assuming the given shift and assuming independence of race outcomes
        B = the density of the statewide shift probability measure at this
            specific shift
    '''
    # find win probability assuming a statewift shift of "shift" in favor of
    # the party
    win_prob = \
        chamber_success_prob_assuming_independence(margins + shift, threshold)
        
    # find relative likelihood of this shift, dividing by statewide_sigma so
    # that the density function integrates to 1     
    shift_prob_density = sts.t.pdf(shift/statewide_sigma, statewide_deg_f) / \
                            statewide_sigma
    
    # return the product
    return win_prob * shift_prob_density
    
def better_chamber_success_prob(margins, threshold, \
                                statewide_sigma=0.04, statewide_deg_f=2):
    ''' Given a list of expected win margins and the number of seats needed
    for the party to have desired redistricting power, find the probability
    of the party reaching that threshold. Considers all statewide shifts and
    assumes independence of errors after the statewide shift. Relies on
    chamber_success_prob_with_shift.
    
    Arguments:
        margins: numpy array of expected win margins (between -1 and 1) for 
            party (negative = loss margin)    
        threshold: number of seats needed for redistricting power
        
    Output: (win_prob, err), where 
        win_prob = real number between 0 and 1, probability of party reaching 
            threshold
        err = error bound on win_prob due to numerical integration error
    '''
    # integrate chamber_success_prob_with_shift with respect to shift from 
    # -inf to +inf
    return quad(chamber_success_prob_with_shift, \
                -np.inf, np.inf, \
                args = (margins, threshold, statewide_sigma, statewide_deg_f))[0]


def voter_power(districts_df, seats_needed):
    ''' Finds the power of one vote in each district (i.e. the increase in
    probability that the party reaches the necessary number of seats if they
    gain one extra vote)
    Arguments:
        districts_df: pandas DataFrame of districts, indexed by 0, 1, 2, ..
            with (at least) these columns:
            'MARGIN': the expected winning margin for the party (negative if
                    losing margin)
            'totalvotes': the number of voters in the district
        seats_needed: number of seats needed for redistricting power
    Output: input DataFrame with one column added, 'VOTER_POWER', which
            gives the result of the calculation for each district'''

    # grab all margins, deep copy in numpy format
    margins = districts_df['MARGIN']
    margins = np.asarray([i for i in margins])

    # find the chamber success probability
    prob = better_chamber_success_prob(margins, seats_needed)
    
    # for all races in districts_df
    for ix, race in districts_df.iterrows():
        
        # grab all margins, deep copy in numpy format
        margins = districts_df['MARGIN']
        margins = np.asarray([i for i in margins])

        # grab the number of voters in the district of interest
        num_voters = race['totalvotes']

        # adjust the margin in that race, assuming the party gained 1 vote
        margins[ix] = margins[ix] + 1 / num_voters

        # NOTE: 1 may be too small, with the effect so small it might get into
        # floating point error. Need to check. Maybe boost to 10 or 100.

        # find the chamber success probability
        prob_new = better_chamber_success_prob(margins, seats_needed)

        # calcuate vote power and add to proper row of districts_df
        districts_df.loc[ix, 'VOTER_POWER'] = prob_new - prob

    return districts_df


def rating_to_margin(favored, confidence, params_file= \
                        'state/rating_to_margin.csv'):
    ''' Gets the expected margin of victory based on information in 
    two input parameter files.
    
    Arguments:
        favored: 'D', 'R', 'I', or FALSE (in case of Toss-Up)
        confidence: 'Toss-Up', 'Tilt', 'Lean', 'Likely', or 'Uncontested'
        params_file: csv with two columns, 'RATING' and 'MARGIN' that give
            expected margin of victory associated with each rating
            
    Output: expected margin of victory, positive if Dem, negative if Rep, None
        if Ind'''        
        
    # read csv into ratings_to_margin DataFrame
    ratings_to_margin_df = pd.read_csv(moneyball_path + params_file, \
                                           index_col='RATING')
    
    # get absolute margin
    margin = ratings_to_margin_df.loc[confidence, 'MARGIN']
    
    # postive if dem, negative if rep, None if ind
    if favored == 'R':
        margin = -margin
    if favored == 'I':
        margin = None
        
    return margin


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
    

def main():
    ratings_df = pd.read_csv(moneyball_path + 'state/state_assembly_turnout.csv')

                                            
    # assume tie = good
    seats_needed = {'TX' : 75, 'KS' : 42, 'NC' : 60, 'FL' : 60}
    output = {}
    for st in seats_needed:
        st_df = ratings_df.loc[ratings_df['state'] == st]
        st_df['MARGIN'] = ''
        st_df['MARGIN'] = ratings_df.apply(lambda x: \
                                              rating_to_margin(x.favored, \
                                                               x.confidence), \
                                               axis=1)
        
        # remove uncontested seats, subtracting dem seats from seats_needed
        threshold = seats_needed[st] - sum(st_df.apply(lambda x: \
                                            x['favored'] == 'D' and \
                                            x['confidence'] == 'Uncontested', \
                                            axis=1))
        st_df = st_df[st_df['confidence'] != 'Uncontested'].reset_index()
        
        output[st] = voter_power(st_df, threshold)
        print (st)
    
    
# if __name__ == "__main__":
#    main()