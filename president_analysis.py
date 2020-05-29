# -*- coding: utf-8 -*-
"""
Created on Thu May 28 15:29:43 2020

@author: Jacob
"""
import pandas as pd
import numpy as np
from datetime import date, timedelta, datetime
from dateutil.parser import parse
from scipy.stats import norm
import matplotlib.pyplot as plt

# download file to dataframe
df = pd.read_csv\
        ("C:\\Users\\Jacob\\Documents\\GitHub\\elections\\raw-polls.csv") 
        
# get rid of this year
df = df[df['year'] != 2020]

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
out_df.set_index('race', inplace=True)

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
out_df['num_polls_used']        
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
out_df['SEM'] = \
            out_df['polls_used'].apply(SEM)
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
    #sem = max(sem, 3)
            
    return np.round(1000*norm.cdf(median/sem))/1000
out_df['win_probability'] = \
            out_df['polls_used'].apply(win_probability)
    
    