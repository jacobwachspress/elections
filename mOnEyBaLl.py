
@author: Jacob
import scipy.stats as sts
from scipy.integrate import quad
    return
    
    

def success_prob_from_meta_margin(meta_margin, meta_sigma=0.03, meta_deg_f=2):
    '''Given the meta-margin for the party reaching the desired threshold and 
    Arguments:
        meta_margin: real number, as calculated by find_meta_margin
        
        meta_sigma: positive real number, estimate of standard deviation of 
        


def success_prob_from_margin(margin, race_sigma=0.03, race_deg_f=2):
    ''' Given the expected margin of a race and the parameters determining the
    t-distribution about this margin, returns the probability of victory.
    
    Arguments:
        margin: real number between -1 and 1, expected win margin for candidate 
            (negative = loss margin)
    
    Output: real number between 0 and 1, probability of candidate winning

    return sts.t.cdf(margin/race_sigma, race_deg_f)

def chamber_success_prob_assuming_independence(margins, threshold):
    ''' Given a list of expected win margins and the number of seats needed
    for the party to have desired redistricting power, find the probability
    and assumes independence of races.
            party (negative = loss margin)
        
        threshold: number of seats needed for redistricting power
        
    Output: probability that the party reaches the threshold number of seats,
    
    probs = [success_prob_from_margin(i) for i in margins]
    
    # associate with each race a polynomial of the form lose_prob + win_prob*x
    # probability of winning exactly n seats
    seat_probs = np.asarray([1])
        seat_probs = np.polymul(seat_probs, poly)
        
    return np.sum(seat_probs[threshold:])

def find_meta_margin(margins, seats_needed):
    ''' Given a list of expected win margins and the number of seats needed
    
    The Meta-Margin is the margin that all seats would have to shift uniformly 
    
    The Meta-Margin isunique because the win probability varies monotonically 
    
    Arguments:
        margins: numpy array of expected win margins for party 
            (negative = loss margin)
            
        seats_needed: number of seats needed for redistricting power
    Output: Meta-Margin 
    ''' 

    # set bounds for Meta-Margin, initialize accuracy threshold eps
    max_margin = 30
    eps = 1e-15
        # find the middle of the range, shift all margins by this amount
        # against the party
        # find the win probability with these shifted margins
        prob = chamber_success_prob_assuming_independence\
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
    
    return success_prob_from_meta_margin(find_meta_margin(margins, threshold))
def chamber_success_prob_with_shift(shift, margins, threshold, \
                                    statewide_sigma = 0.03, statewide_deg_f=2):
        shift: real number between -1 and 1, how much all seats the state are 
            shifted in favor of the party 
            party before the statewide shift (negative = loss margin)
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
    shift_prob_density = sts.t.pdf(shift/statewide_sigma, statewide_deg_f) / \
                            statewide_sigma
    return win_prob * shift_prob_density
    
def better_chamber_success_prob(margins, threshold, \
    assumes independence of errors after the statewide shift. Relies on
    chamber_success_prob_with_shift.
    Arguments:
        margins: numpy array of expected win margins (between -1 and 1) for 
        
        threshold: number of seats needed for redistricting power
        win_prob = real number between 0 and 1, probability of party reaching 
            threshold
    # integrate chamber_success_prob_with_shift with respect to shift from 
    probability that the party reaches the necessary number of seats if they gain
    one extra vote) 
        districts_df: pandas DataFrame of districts, indexed by 0, 1, 2, ..
            with (at least) these columns:
            'MARGIN': the expected winning margin for the party (negative if 
                    losing margin)
            'NUM_VOTERS': the number of voters in the district
            
        seats_needed: number of seats needed for redistricting power 
        
    # for all races in districts_df
    for ix, race in districts_df.iterrows():
        margins = districts_df['MARGIN']
        margins = np.asarray([i for i in margins])
        
        # find the chamber success probability 
        prob = better_chamber_success_prob(margins, seats_needed)
        
        
        # adjust the margin in that race, assuming the party gained 1 vote
        ## NOTE: 1 may be too small, with the effect so small it might get into 
        ## floating point error. Need to check. Maybe boost to 10 or 100.
        
