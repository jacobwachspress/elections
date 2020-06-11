# -*- coding: utf-8 -*-
"""
Created on Thu Jun 11 14:04:26 2020

@author: Jacob
"""
import scipy.stats as sts
import numpy as np

def margins_from_ratings(ratings):
    return
    
    
''' Given the meta-margin for the party reaching the desired threshold and the 
parameters determining the t-distribution about this margin, returns the 
party's probability of reaching this threshold.

Arguments:
    meta_margin: real number, as calculated by find_meta_margin
    meta_sigma: positive real number, estimate of standard deviation of 
        actual meta-margin
    race_df: positive integer, degrees of freedom used in t-distribution
Output:
    prob: real number between 0 and 1, probability of party reaching threshold
'''
def win_probability_from_meta_margin(meta_margin, meta_sigma=3, meta_df=2):
    return sts.t.cdf(meta_margin/meta_sigma, meta_df)

''' Given the expected margin of a race and the parameters determining the
t-distribution about this margin, returns the probability of victory.

Arguments:
    margin: real number, expected win margin for candidate 
        (negative = loss margin)
    race_sigma: positive real number, estimate of standard deviation of actual 
        win margin
    race_df: positive integer, degrees of freedom used in t-distribution
Output:
    prob: real number between 0 and 1, probability of candidate winning
'''
def prob_from_margin(margin, race_sigma=3, race_df=2):
    return sts.t.cdf(margin/race_sigma, race_df)
    
''' Given a list of expected win margins and the number of seats needed
for the party to have desired redistricting power, find the probability
of the party reaching that threshold.

Arguments:
    margins: numpy array of expected win margins for party 
        (negative = loss margin)
    threshold: number of seats needed for redistricting power
Output:
    prob: probability that the party reaches the threshold number of seats,
        assuming independence of race outcomes
'''
def chamber_win_probability_assuming_independence(margins, threshold):
    
    # find probability of victory for each race
    probs = [prob_from_margin(i) for i in margins]
    
    ## Find full probability distribution of seats won, assuming independence ##
    
    # associate with each race a polynomial of the form lose_prob + win_prob*x
    polys = [np.asarray([1-p, p]) for p in probs]
    
    # multiply all of these polynomials; the resulting coefficient of x^n
    # is the nth element of the list (index starting at 0), and is the 
    # probability of winning exactly n seats
    seat_probs = np.asarray([1])
    for poly in polys:
        seat_probs = np.polymul(seat_probs, poly)
        
    # return the probability of reaching the threshold
    return np.sum(seat_probs[threshold:])

''' Given a list of expected win margins and the number of seats needed
for the party to have desired redistricting power, finds the meta-margin

Arguments:
    margins: numpy array of expected win margins for party 
        (negative = loss margin)
    seats_needed: number of seats needed for redistricting power
Output:
    meta_margin: the margin that all seats would have to shift uniformly so 
        that the probability of the party reaching that threshold is exactly 
        50 percent (by convention, positive meta_margin implies the party is
        favored)
'''    
def find_meta_margin(margins, seats_needed):
    ## Idea: use bisection to estimate the meta-margin numerically, it is 
    ## unique because the win probability varies monotonically with
    ## the uniform shift.
    
    # set bounds for meta margin, initialize accuracy threshold eps
    min_margin = -30
    max_margin = 30
    eps = 1e-15
    
    # while we still have a range of uncertainty of length at least eps
    while max_margin - min_margin > eps:
        
        # find the middle of the range, shift all margins by this amount
        # against the party
        average = (min_margin + max_margin)/2
        adjusted_margins = margins - average
        
        # find the win probability with these shifted margins
        prob = chamber_win_probability_assuming_independence\
                    (adjusted_margins, seats_needed)
                    
        # depending on whether this probability is below or above 0.5, 
        # modify the search bounds appropriately
        if prob < 0.5:
            max_margin = average
        else:
            min_margin = average
    
    # return an endpoint of the interval, which has converged to a point
    return min_margin
    