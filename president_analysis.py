# -*- coding: utf-8 -*-
"""
Created on Thu May 28 15:29:43 2020

@author: Jacob
"""
import pandas as pd
import numpy as np
from datetime import date, timedelta, datetime
from dateutil.parser import parse
import scipy.stats as st
from scipy.stats import norm
import matplotlib.pyplot as plt
from sklearn.calibration import calibration_curve

# download EV file
ev = pd.read_csv("C:\\Users\\Jacob\\Documents\\GitHub\\elections\\ev.csv")
ev.set_index('State', inplace=True)

# download file to dataframe
df = pd.read_csv\
        ("C:\\Users\\Jacob\\Documents\\GitHub\\elections\\raw-polls.csv") 
        
# get rid of this year, national polls
df = df[df['year'] != 2020]
df = df[df['location'] != 'US']

# put 'polldate' column in datetime date format
def format_date(i):
    return parse(i).date()
df['polldate'] = df['polldate'].apply(format_date)
    
# restrict to specific type of race
race_type = 'Pres-G'
df = df[df['type_simple'] == race_type]

# get all races polled, at all levels where they were polled
# for example, the 2004 presidential race in FL is different from the
# 2004 presidential race in MI
races = list(set(df['race']))

# initialize output df
out_df = pd.DataFrame({'race': races})
out_df['polls_used'] = ''
out_df['num_polls_used'] =''
out_df['median_winning_margin'] = ''
out_df['median_absolute_deviation'] = ''
out_df['SEM'] = ''
out_df['win_probability'] = ''
out_df['actual_winning_margin'] = ''
out_df['error_of_median'] = ''
out_df['won_race'] = ''
out_df['year'] = ''
out_df['state'] = ''
out_df.set_index('race', inplace=True)

# set year and state field
for i, _ in out_df.iterrows():
    out_df.loc[i, 'year'] = int(i[0:4])
    out_df.loc[i, 'state'] = i[-2:]

# Determine which polls to use according to the following rules:
# 1. Consider only the most recent poll for a given pollster
#
# 2. Use all polls taken in the two weeks prior to election day, or use the
# last three polls, whichever gives more data

# for each race
for race in races:
    
    # splice DataFrame to only consider polls from this race
    race_df = df[df['race'] == race]
    
    # find the year
    year = list(race_df['year'])[0]
    
    # find general election day on this year, the Tuesday in the range 11/2-11/8 
    for day in [2, 3, 4, 5, 6, 7, 8]:
        if date(year, 11, day).weekday() == 1:
            election_day = date(year, 11, day)
    

    ## Filter out earlier polls by same pollster
    
    pollsters = list(set(race_df['pollster_rating_id']))
    
    # for each pollster
    for pollster in pollsters:
        
        # find the last date among their polls
        pollster_df = race_df[race_df['pollster_rating_id'] == pollster]
        last_date = sorted(pollster_df['polldate'])[-1]
        
        # delete all polls from this pollster that do not occur on this date
        race_df = race_df[(race_df['pollster_rating_id'] != pollster) | \
                          (race_df['polldate'] == last_date)]
    
    # Find all polls in the 14 days before election day
    def time_to_election(i):
        return (election_day - i).days
    last_14_df = race_df[race_df['polldate'].apply(time_to_election) <= 14]
    
    # if there are at least 3 such polls
    if len(last_14_df) >= 3:
        # use these polls
        out_df.loc[race]['polls_used'] = last_14_df
        
    # if there are less than 3 such polls
    else:
        # sort the polls earliest to latest
        race_df = race_df.sort_values(by='polldate')
        # use the last 3 polls
        out_df.loc[race]['polls_used'] = race_df[-3:]
        
## Fill in the remaining columns of out_df based on the polls used

# number of polls used
out_df['num_polls_used'] = out_df['polls_used'].apply(len)
 
# median winning margin in polls of candidate 1
def median_win_margin(polls_df):
    return np.median(np.asarray(polls_df['cand1_pct'] - polls_df['cand2_pct']))
out_df['median_winning_margin'] = out_df['polls_used'].apply(median_win_margin)

# median absolute deviation from median 
def median_deviation(polls_df):
    margins = np.asarray(polls_df['cand1_pct'] - polls_df['cand2_pct'])
    median = np.median(margins)
    deviations = np.abs(margins - median)
    return np.median(deviations)
out_df['median_absolute_deviation'] = \
            out_df['polls_used'].apply(median_deviation)
            

# this formula is per Sam's documentation, where he says we calculate the 
# standard error of the mean, but with the median in place of the mean
# and (median absolute deviation from median)/0.675 in place of the stanard
# deviation
def SEM(polls_df):
    med_deviation = median_deviation(polls_df)
    
    
    stddev = med_deviation / 0.675
    
    return stddev / np.sqrt(len(polls_df))
out_df['SEM'] = out_df['polls_used'].apply(SEM)

# win probability of candidate 1
# we find the probability that a Gaussian random variable with 
# distruibuted according to ~ N(median, SEM) is greater than 0.    
def win_probability(polls_df):
    median = median_win_margin(polls_df)
    sem = SEM(polls_df) 
    # the absurd case where SEM = 0
    if sem == 0:
        sem = 0.0001
        
    # 2020 modification, require SEM >= 3
    sem = 3
            
    return np.round(1000*norm.cdf(median/sem))/1000
out_df['win_probability'] = \
            out_df['polls_used'].apply(win_probability)
    
# actual win margin
def actual_win_margin(polls_df):
    return max(polls_df['cand1_actual']) - max(polls_df['cand2_actual'])  
out_df['actual_winning_margin'] = out_df['polls_used'].apply(actual_win_margin)

# error of the polling median
out_df['error_of_median'] = \
    out_df['median_winning_margin'] - out_df['actual_winning_margin'] 
# won race
def won_race(margin):
    return margin > 0 
out_df['won_race'] = out_df['actual_winning_margin'].apply(won_race)

# drop polls used
out_df = out_df.drop(columns=['polls_used'])


### SOME TESTING (TRASH) ###
def win_prob_2(race):
    m = race['median_winning_margin']
    n = race['num_polls_used']
    return st.t.cdf(m*(n+3)/(2*n+26), 10)
for i, race in out_df.iterrows():
    out_df.loc[i, 'win_probability'] = win_prob_2(race)

    
def calibrate():
    probs = []
    actuals = []
    for percent in np.linspace(0, 1, 101):
        idxs = [i for i, x in out_df.iterrows() if out_df.loc[i, 'win_probability'] <= percent+0.1 and out_df.loc[i, 'win_probability'] >= percent-0.1]
        probs.append(np.mean([out_df.loc[i, 'win_probability'] for i in idxs]))
        actuals.append(sum([out_df.loc[i, 'won_race'] for i in idxs])/len([out_df.loc[i, 'won_race'] for i in idxs]))
    return probs, actuals

# calculates the average polling error in a year, weighted roughly by population
def weighted_national_error(year):
    # set year for electoral votes
    if year > 2010:
        ev_year = '2010'
    else:
        ev_year = '2000'
        
    year_df = out_df[out_df['year'] == year]
    year_df = year_df[year_df['state'].isin(list(ev.index))]
    errors = [year_df.loc[race, 'error_of_median'] for race, _ in year_df.iterrows()]
    evs = [ev.loc[i['state'], ev_year] for race, i in year_df.iterrows()]
    
    # find average
    return sum(np.asarray(errors) * (np.asarray(evs) - 2)) / np.sum(np.asarray(evs) - 2)

out_df['adjusted_error_of_median'] = out_df['error_of_median'] - out_df['year'].apply(weighted_national_error)
