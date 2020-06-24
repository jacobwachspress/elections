# -*- coding: utf-8 -*-
"""
Created on Thu Jun 11 14:04:26 2020
@author: Jacob
"""
import scipy
import scipy.stats as sts
from scipy.integrate import quad, nquad
import numpy as np
import pandas as pd

# MONEYBALL PATH FOR GOOGLE DRIVE
moneyball_path = 'G:/Shared drives/princeton_gerrymandering_project/Moneyball/'
count = 0

def prob_from_margin(margin, race_sigma, race_deg_f):
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
    return sts.t.cdf(margin / race_sigma, race_deg_f)


def success_prob_independence(margins, threshold, race_sigma, race_deg_f):
    ''' Given a list of expected win margins and the number of seats needed
    for the party to have desired redistricting power, find the probability
    of the party reaching that threshold. Relies on prob_from_margin
    and assumes independence of races.
    Arguments:
        margins: numpy array of expected win margins (between -1 and 1) for
            party (negative = loss margin)
        threshold: number of seats needed for redistricting power
        race_sigma: positive real number, estimate of standard deviation of
            actual win margin in each race
        race_df: positive integer, degrees of freedom used in t-distribution
            in each race
    Output: probability that the party reaches the threshold number of seats,
            assuming independence of race outcomes
    '''

    # find probability of victory for each race
    probs = [prob_from_margin(i, race_sigma, race_deg_f) for i in margins]

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

def chamber_success_prob_with_shift(*args):
    ''' Helper method to be integrated in chamber_success_prob. Takes a
    variable number of arguments in order to comply with the specifications
    of scipy.integrate.nquad and allow any number of independent shifts.
    
    Arguments: x_1, x_2, x_3, ... , x_n, threshold, race_sigma, race_deg_f, 
            parameter_weights, sigmas, deg_fs (in this order). 
            
        x_1, ... , x_n denote shifts in n parameters of correlated error
            among n independent categories (i.e. rural, statewide, incumbent)
        threshold: number of seats needed for redistricting power
        race_sigma: positive real number, estimate of standard deviation of
            actual win margin in each race, after correlated error
        race_df: positive integer, degrees of freedom used in t-distribution
            in each race
        parameter_weights: numpy matrix with n+1 columns, where the rows denote
            races, the first column denotes the desired candidate's expected
            win margin, and the remaining columns denote the margin's
            sensitivity to an error in a certain parameter 
        sigmas: numpy array with n elements, where element i corresponds to
            the sigma of the t-distribution for the error of the random
            variable whose category is in the (i+1)st column of 
            parameter_weights
        deg_fs: corresponding degrees of freedom for the t-distribution 
            (indexed the same as sigmas)
            
    Output: A*B, where
        A = probability of party reaching threshold under this shift
        B = probability density of this set of shifts

    '''
    # parse args
    threshold = args[-6]
    race_sigma = args[-5]
    race_deg_f = args[-4]
    parameter_weights = args[-3]
    sigmas = args[-2]
    deg_fs = args[-1]
    shift_vector = list(args[0:-6])
            
    # check that parameters have the right sizes, for the ones that won't get 
    # caught automatically later
    n = len(sigmas)
    assert len(deg_fs) == n, "deg_fs and sigmas not same size"
    assert len(shift_vector) == n, "shift_vector and sigmas not same size"
    
    # find expected margins before independent race shift
    # append 1 at the beginning to add in the starting margin
    margins = parameter_weights.dot(np.asarray([1] + shift_vector))
    
    # find win probability assuming this set of correlated shifts
    win_prob = success_prob_independence(margins, threshold, \
                                                   race_sigma, race_deg_f)
                
    # find relative likelihood of this shift, dividing by all sigmas so
    # that the density function integrates to 1    
    densities = [sts.t.pdf(shift_vector[i] / sigmas[i], deg_fs[i]) for i \
                     in range(len(shift_vector))]
    shift_prob_density = np.prod(densities) / np.prod(sigmas)
    
    # return the product
    return win_prob * shift_prob_density
    
def chamber_success_prob(parameter_weights, t_dist_params, threshold, \
                             race_sigma, race_deg_f):
    ''' TODO COMMENT THIS
    '''
    # build range array for all variables
    n = len(t_dist_params)
    range_arr = [[-np.inf, np.inf] for i in range(n)]
    
    # extract sigmas and deg_fs from t_dist_params
    sigmas = [param[0] for param in t_dist_params]
    deg_fs = [param[1] for param in t_dist_params]
    
    # integrate chamber_success_prob_with_shift with respect to all shift 
    # variables from -inf to +inf
    return nquad(chamber_success_prob_with_shift, range_arr, \
                args = (threshold, race_sigma, race_deg_f, \
                        parameter_weights, sigmas, deg_fs))

## TODO NEEDS REWRITE ##
def voter_power(districts_df, error_vars, threshold, race_sigma, race_deg_f, \
                        total_votes='totalvotes'):
    ''' Finds the power of one vote in each district (i.e. the increase in
    probability that the party reaches the necessary number of seats if they
    gain one extra vote)
    Arguments:
        districts_df: pandas DataFrame of districts, indexed by 0, 1, 2, ..
            with (at least) these columns:
            'MARGIN': the expected winning margin for the party (negative if
                    losing margin)
            'totalvotes': the number of voters in the district
        threshold: number of seats needed for redistricting power
    Output: input DataFrame with one column added, 'VOTER_POWER', which
            gives the result of the calculation for each district'''
            
    # generate parameter_weights, must have columns[0] be the margins
    parameter_weights = districts_df[error_vars].to_numpy()
    
    # get total_votes by district
    votes_by_district  = list(districts_df[total_votes])
    
    # extract sigmas, deg_fs from error_vars
    t_dist_params = list(error_vars.values()) 

    # find the chamber success probability
    prob = chamber_success_prob(parameter_weights, t_dist_params, threshold, \
                             race_sigma, race_deg_f)
    
    # intitialize voter_powers list
    voter_powers = []
    
    # for all races
    for i in range(len(parameter_weights[:,0])):
        
        # deep copy parameter_weights
        param_weights_copy = parameter_weights.copy()

        # grab the number of voters in the district of interest
        num_voters = votes_by_district[i]

        # adjust the margin in that race, assuming the party gained 1 vote
        param_weights_copy[i, 0] = param_weights_copy[i, 0] + 1/num_voters

        # NOTE: 1 may be too small, with the effect so small it might get into
        # floating point error. Need to check. Maybe boost to 10 or 100.

        # find the chamber success probability
        prob_new = chamber_success_prob(param_weights_copy, t_dist_params, \
                                        threshold, race_sigma, race_deg_f)

        # calcuate vote power and add to proper row of districts_df
        voter_powers[i] = prob_new - prob

    districts_df['VOTER_POWER'] = voter_powers
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
        st_df['MARGIN'] = st_df.apply(lambda x: \
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