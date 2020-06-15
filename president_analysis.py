"""
Created on Thu May 28 15:29:43 2020

@author: Jacob
"""
import pandas as pd
import numpy as np
from scipy.stats import norm
from datetime import datetime as dt
from datetime import timedelta


def within_14(election_day, poll_day):
    """Check if poll day is within two weeks of election day"""
    return election_day - timedelta(days=14) < poll_day


# median winning margin in polls of candidate 1
def median_win_margin(polls_df):
    """Extract the median margin."""
    return np.median(np.asarray(polls_df['cand1_pct'] - polls_df['cand2_pct']))


def median_deviation(polls_df):
    """Calculate median absolute deviation (MAD)."""
    margins = np.asarray(polls_df['cand1_pct'] - polls_df['cand2_pct'])
    median = np.median(margins)
    deviations = np.abs(margins - median)
    return np.median(deviations)


def SEM(polls_df):
    """Standard error of the mean.

    To prevent errors from outliers. Use th emedian in place of the mean and
    the MAD / 0.675 in place of the standard deviation.
    """
    med_deviation = median_deviation(polls_df)
    stddev = med_deviation / 0.675
    return stddev / np.sqrt(len(polls_df))


def win_prob(polls_df):
    """Assume normal dist and calculute probability candidate 1 wins."""
    median = median_win_margin(polls_df)
    sem = SEM(polls_df)

    # Require SEM >= 3
    sem = np.maximum(sem, 3)

    # Get the probability from a normal distribution
    return np.round(1000 * norm.cdf(median / sem)) / 1000


def actual_win_margin(polls_df):
    """Use max since all actual results are equal to get result margin."""
    return max(polls_df['cand1_actual']) - max(polls_df['cand2_actual'])


def main():
    """Perform presidential voter power analysis."""
    # import electoral votes and polls
    ev = pd.read_csv('ev.csv').set_index('State')
    df = pd.read_csv('raw-polls.csv')

    # Only use state polls before 2020
    df = df[(df['year'] < 2020) & (df['location'] != 'US')]

    # Make polldate attribute a datetime
    df['polldate'] = df['polldate'].apply(lambda x: dt.strptime(x, '%m/%d/%Y'))

    # Only use president general polls
    df = df[df['type_simple'] == 'Pres-G']

    # Create dataframe for each relevant race attribute. For example the 04
    # FL pres. race will have a different label than the 04 MI pres. race
    races = list(set(df['race']))
    out_cols = ['race', 'polls_used', 'num_polls', 'median_win_marg', 'MAD',
                'SEM', 'win_prob', 'actual_win_marg', 'error_of_median',
                'won_race', 'year', 'state']
    out_df = pd.DataFrame({'race': races}, columns=out_cols).fillna('')

    # Set year and state
    out_df['year'] = out_df['race'].apply(lambda x: x[0:4])
    out_df['state'] = out_df['race'].apply(lambda x: x[-2:])

    # Set index to race
    out_df = out_df.set_index('race')

    # Determine which polls to use according to the following rules:
    # 1. Consider only the most recent poll for a given pollster
    #
    # 2. Use all polls taken in the two weeks prior to election day, or use the
    # last three polls, whichever gives more data

    for race in races:
        # only consider polls from the current race
        race_df = df[df['race'] == race]

        # Get the year of the race
        year = list(race_df['year'])[0]

        # Extract general election day
        for day in [2, 3, 4, 5, 6, 7, 8]:
            if dt(year, 11, day).weekday() == 1:
                elec_day = dt(year, 11, day)
                break

        # Filter out earlier polls
        for pollster in race_df['pollster_rating_id'].unique():
            # find the last date of the pollster
            pollster_df = race_df[race_df['pollster_rating_id'] == pollster]
            last_date = sorted(pollster_df['polldate'])[-1]

            # Delete all polls from this pollster before this date
            race_df = race_df[(race_df['pollster_rating_id'] != pollster) |
                              (race_df['polldate'] == last_date)]

            # Get all polls 14 days before election day
            last_14_df = race_df[race_df['polldate'].apply(lambda x:
                                                           within_14(elec_day,
                                                                     x))]

            # Save polls used in the output dataframe
            # if there are at least 3 polls keep the last_14_df
            if len(last_14_df) >= 3:
                out_df.loc[race]['polls_used'] = last_14_df
            # if there are less than 3 polls within 14 days keep last 3 polls
            else:
                race_df = race_df.sort_values(by='polldate')
                out_df.loc[race]['polls_used'] = race_df[-3:]

    # The remaining attributes in out_df will be filled using the polls
    # we saved in the polls_used attribute

    # Get the (1) number of polls, (2) median winning margin, (3) mean absolute
    # deviation, (4) standard error of the mean, but with the median and
    # median absolute deviation
    out_df['num_polls'] = out_df['polls_used'].apply(len)
    out_df['median_win_marg'] = out_df['polls_used'].apply(median_win_margin)
    out_df['MAD'] = out_df['polls_used'].apply(median_deviation)
    out_df['SEM'] = out_df['polls_used'].apply(SEM)

    # Calculate the win probability of candidate 1
    out_df['win_prob'] = out_df['polls_used'].apply(win_prob)

    # Get the actual winning margin
    out_df['actual_win_marg'] = out_df['polls_used'].apply(actual_win_margin)

    # Get the error of the polling median
    out_df['error_of_median'] = out_df['median_win_marg']
    out_df['error_of_median'] -= out_df['actual_win_marg']

    # Boolean if candidate 1 won the race
    out_df['won_race'] = (out_df['actual_win_marg'] > 0)

    # Apply buckets for calibration
    bins = np.linspace(-0.01, 1, 102)
    out_df['bucket_ix'] = pd.cut(out_df['win_prob'], bins, labels=False)

    # Remove the polls used
    out_df = out_df.drop(columns=['polls_used'])

    # Calculate the weighted national error and join. This will calculate the
    # average polling error in a year and is weighted by electoral votes - 2
    nat_err_df = pd.DataFrame()
    for year in out_df['year'].unique():
        # Get the correct year for electoral votes
        if int(year) > 2010:
            ev_year = '2010'
        else:
            ev_year = '2000'

        # Get the out_df for the specific year
        year_df = out_df[out_df['year'] == year]
        year_df = year_df[year_df['state'].isin(list(ev.index))]
        errors = [year_df.loc[race, 'error_of_median']
                  for race, _ in year_df.iterrows()]
        evs = [ev.loc[i['state'], ev_year] for race, i in year_df.iterrows()]

        # Get average error using population estimate
        pop_est = np.array(evs) - 2
        avg_error = np.dot(np.array(errors), pop_est) / np.sum(pop_est)
        nat_err_df.at[year, 'wt_national_error'] = avg_error

    # Join to add weighted national error to out_df
    out_df = out_df.merge(nat_err_df, left_on='year', right_index=True)

    # Calculate the adjusted error of the median
    out_df['adj_error_of_median'] = out_df['error_of_median']
    out_df['adj_error_of_median'] -= out_df['wt_national_error']
    return out_df


if __name__ == "__main__":
    main()
