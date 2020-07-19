"""Pull Incumbency Data for State Legislative Upper Chambers.

We need to know who holds seats that are not up for election.

We do not pull data for MI, NE, and NH because they are not high leverage
for this project and their wikipedia tables are inherently different in
structure.
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd


def main():
    """Scrape."""
    # Get states dictionary
    states = states_dict()

    # Define base url and additions for the two separate websites
    url = 'https://en.wikipedia.org/wiki/List_of_U.S._state_representatives_'
    site1 = '(Alabama_to_Missouri)'
    site2 = '(Montana_to_Wyoming)'

    # Pull from first website
    page = requests.get(url + site1)
    soup = BeautifulSoup(page.content, 'html.parser')

    # Get the text that references the senator list
    indiv_text = 'div-col columns column-width'

    # Initialize dataframe that will contain relevant data
    df_inc = pd.DataFrame()

    # Iterate through the systematic states
    for abbrev, state in states.items():
        # Reload second website once we get to montana
        if state == 'Montana':
            page = requests.get(url + site2)
            soup = BeautifulSoup(page.content, 'html.parser')

        # Get the relevant state wikipedia table
        label = 'Members_of_the_' + state + '_House_of_Representatives'
        state_table = soup.findAll('div', {'aria-labelledby': label})

        # Second Type of Label
        if len(state_table) == 0:
            label = 'Members_of_the_' + state + '_State_Assembly'
            state_table = soup.findAll('div', {'aria-labelledby': label})

        # Third type of label for tables
        if len(state_table) == 0:
            label = 'Members_of_the_' + state + '_House_of_Delegates'
            state_table = soup.findAll('div', {'aria-labelledby': label})

        # Fourth type of label for tables
        if len(state_table) == 0:
            label = 'Current_members_of_the_' + state
            label += '_House_of_Representatives'
            state_table = soup.findAll('div', {'aria-labelledby': label})

        # Fifth type of label for tables
        if len(state_table) == 0:
            label = 'Members_of_the_' + state + '_General_Assembly'
            state_table = soup.findAll('div', {'aria-labelledby': label})

        # Get the list of individuals
        rep_list = state_table[0].findAll('div', {'class': indiv_text})[0]
        rep_list = rep_list.find_next('ol').find_all('li')

        # Iterate through the list of senators
        for ix, elem in enumerate(rep_list):
            # Get the candidate and the party
            text = elem.text.strip()
            candidate = text.split('(')[0].strip()
            party = text.split()[-1][1]

            # Save candidate data (wikipedia orders according to district)
            r = len(df_inc)
            df_inc.at[r, 'state'] = abbrev
            df_inc.at[r, 'candidate'] = candidate
            df_inc.at[r, 'party'] = party
            df_inc.at[r, 'district'] = ix + 1

    # Change vacant seats to no party
    vacant = ['Vacant', 'vacant', '--Vacant--', 'seat vacant']
    df_inc.loc[df_inc['candidate'] == '', 'candidate'] = 'Vacant'
    df_inc.loc[df_inc['candidate'].isin(vacant), 'party'] = False

    # Save to drive
    path = 'G:/Shared drives/princeton_gerrymandering_project/Moneyball/'
    path += 'fundamentals/clean/state_lower_chamber_incumbency.csv'
    df_inc.to_csv(path, index=False)
    return


def states_dict():
    """Return dictionary of state abbreviation mapping to Wikipedia name."""
    states = {}
    states['AL'] = 'Alabama'
    states['AK'] = 'Alaska'
    states['AZ'] = 'Arizona'
    states['AR'] = 'Arkansas'
    states['CA'] = 'California'
    states['CO'] = 'Colorado'
    states['CT'] = 'Connecticut'
    states['DE'] = 'Delaware'
    states['FL'] = 'Florida'
    states['GA'] = 'Georgia'
    states['HI'] = 'Hawaii'
    states['ID'] = 'Idaho'
    states['IL'] = 'Illinois'
    states['IN'] = 'Indiana'
    states['IA'] = 'Iowa'
    states['KS'] = 'Kansas'
    states['KY'] = 'Kentucky'
    states['LA'] = 'Louisiana'
    states['ME'] = 'Maine'
    states['MD'] = 'Maryland'
    states['MA'] = 'Massachusetts'
    states['MI'] = 'Michigan'
    states['MN'] = 'Minnesota'
    states['MS'] = 'Mississippi'
    states['MO'] = 'Missouri'
    states['MT'] = 'Montana'
    states['NV'] = 'Nevada'
    states['NJ'] = 'New_Jersey'
    states['NM'] = 'New_Mexico'
    states['NY'] = 'New_York'
    states['NC'] = 'North_Carolina'
    states['ND'] = 'North_Dakota'
    states['OH'] = 'Ohio'
    states['OK'] = 'Oklahoma'
    states['OR'] = 'Oregon'
    states['PA'] = 'Pennsylvania'
    states['RI'] = 'Rhode_Island'
    states['SC'] = 'South_Carolina'
    states['SD'] = 'South_Dakota'
    states['TN'] = 'Tennessee'
    states['TX'] = 'Texas'
    states['UT'] = 'Utah'
    states['VT'] = 'Vermont'
    states['VA'] = 'Virginia'
    states['WA'] = 'Washington'
    states['WV'] = 'West_Virginia'
    states['WI'] = 'Wisconsin'
    states['WY'] = 'Wyoming'
    return states


if __name__ == "__main__":
    main()