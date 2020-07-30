"""Clean Errors in MEDSL state legislative results in 2018."""
from clean_moneyball import massachusetts_cleaning
import pandas as pd


def main():
    """Get historical incumbency unavailable in cnalysis rating."""
    # Get election results
    df = pd.read_csv('data/input/election/medsl_state_results_2018.csv',
                     encoding='ISO-8859-1')

    # Get data error corrections
    party_path = 'data/input/foundation/medsl_party_corrections.csv'
    results_path = 'data/input/foundation/medsl_results_corrections.csv'
    df_party = pd.read_csv(party_path)
    df_results = pd.read_csv(results_path)

    # Load 2018 election results and hand checked incumbency
    df_elec_18 = clean_results_18(df, df_party, df_results)
    elec_path = 'data/output/electoins/state_results_2018.csv'
    df_elec_18.to_csv(elec_path, index=False)
    return


def clean_results_18(df, df_party, df_results):
    """Clean MIT electin lab election results in 2018.

    Arguments:
        df: MIT election data

        df_party: party error corrections for MIT data

        df_results: election result "corrections", sometimes just using most
                    recent special election or fixing corner cases
    """

    # Update party of each candidate
    for ix, row in df_party.iterrows():
        df.loc[df['candidate'] == row['candidate'],
               'party'] = row['actual_party']

    # Add updated results for each candidate
    for ix, row in df_results.iterrows():
        df = df[~((df['district'] == row['district']) &
                (df['state_po'] == row['state_po']) &
                (df['office'] == row['office']))]
    df = df.append(df_results)

    # Define relevant offices
    partial_term = 'State Representative (Partial Term Ending 01/01/2019)'
    relevant_offices = ['House of Delegates Member', 'State Assembly Member',
                        'State Assembly Representative',
                        'State House Delegate', 'State Representative',
                        partial_term, 'State Representative A',
                        'State Representative B',
                        'State Representative Pos. 1',
                        'State Representative Pos. 2', 'State Senate',
                        'State Senator',
                        'State Senator Partial Term Ending (01/01/2019)']
    senate_offices = ['State Senate', 'State Senator',
                      'State Senator Partial Term Ending (01/01/2019)']
    df = df[df['office'].isin(relevant_offices)]

    # Identify which chamber each race is
    df['chamber'] = df['office'].apply(lambda x: 'upper' if x in senate_offices
                                       else 'lower')

    # let state be the abbreviation
    df['state'] = df['state_po']

    # Filter out WV, VT, and NH because of multi-member districts
    df = df[~df['state'].isin(['WV', 'VT', 'NH'])]

    # keep relevant columns
    keep_cols = ['year', 'state', 'chamber', 'district', 'candidate',
                 'party', 'candidatevotes']
    df = df[keep_cols]
    df = df.sort_values(by=['state', 'district'])

    # Sum candidate votes
    group_cols = ['year', 'state', 'chamber', 'district', 'candidate', 'party']
    df = df.groupby(group_cols).sum()

    # Get the actual party of each candidate
    df = df.reset_index()
    df_candidate = df.sort_values(by='candidatevotes', ascending=False)
    dup_cols = ['state', 'chamber', 'district', 'candidate']
    df_candidate = df_candidate.drop_duplicates(subset=dup_cols)
    df_candidate = df_candidate.drop('candidatevotes', axis=1)

    # Get the votes per candidate in each race and add back party
    group_cols = ['year', 'state', 'chamber', 'district', 'candidate']
    df = df.groupby(group_cols).sum()
    df = df.reset_index()
    df = df.merge(df_candidate)

    # Get top candidate for each party
    df = df.sort_values(by='candidatevotes', ascending=False)
    duplicate_cols = ['year', 'state', 'chamber', 'district', 'party']
    df = df.drop_duplicates(subset=duplicate_cols)

    # Change MN democratic-farmer-labor to democrat
    df.loc[(df['party'] == 'democratic-farmer-labor') &
           (df['state'] == 'MN'), 'party'] = 'democrat'
    df.loc[(df['party'] == 'democratic-npl') &
           (df['state'] == 'MN'), 'party'] = 'democrat'

    # Rename all other parties as independent
    df['party'] = df['party'].apply(lambda x: x if x in ['democrat',
                                                         'republican']
                                    else 'independent')

    # Pivot the table for votes
    df_votes = df.pivot_table(values='candidatevotes', columns='party',
                              index=['year', 'state', 'chamber', 'district'])
    df_votes = df_votes.fillna(0)
    df_votes = df_votes.reset_index()

    # Pivot the table for candidates
    df_cand = df.pivot_table(values=['candidate'], columns='party',
                             index=['year', 'state', 'chamber', 'district'],
                             aggfunc=lambda x: ' '.join(x))
    df_cand.columns = df_cand.columns.droplevel()
    df_cand.columns = ['dem_cand', 'ind_cand', 'rep_cand']
    df_cand = df_cand.reset_index()

    # Join candidate and votes
    df = df_votes.merge(df_cand)

    # Get 3 party voteshare
    df['three_sum'] = df['democrat'] + df['independent'] + df['republican']
    df['dem_three'] = df['democrat'] / df['three_sum']
    df['ind_three'] = df['independent'] / df['three_sum']
    df['rep_three'] = df['republican'] / df['three_sum']

    # Get 2 party voteshare
    df['two_sum'] = df['democrat'] + df['republican']
    df['dem_two'] = df['democrat'] / df['two_sum']
    df['rep_two'] = df['republican'] / df['two_sum']
    df = df.drop(columns=['two_sum', 'three_sum'])

    # hardcoded cleaning (HI one-off and UT one-off matching errors)
    df['district'] = df['district'].apply(lambda x: 'District 19'
                                          if x == 'District 19 Vacancy' else x)
    df['district'] = df['district'].apply(lambda x: 'District 8'
                                          if x == 'District 8 (2 year term)'
                                          else x)

    # Get district number for MA
    mass_dict_L, mass_dict_U, _, _ = massachusetts_cleaning()
    df_ma = df[df['state'] == 'MA']
    df_ma_L = df_ma[df_ma['chamber'] == 'lower']
    df_ma_U = df_ma[df_ma['chamber'] == 'upper']
    df_ma_L['district_num'] = df_ma_L['district'].apply(lambda x:
                                                        str(mass_dict_L[x]))
    df_ma_U['district_num'] = df_ma_U['district'].apply(lambda x:
                                                        str(mass_dict_U[x]))

    # Get district num for every other state
    df = df[df['state'] != 'MA']
    df['district_num'] = df['district'].apply(lambda x: x.split(' ')[-1])

    # Append back together
    df = df.append(df_ma_U).append(df_ma_L)
    df['district_num'] = df['district_num'].str.zfill(3)
    return df


if __name__ == "__main__":
    main()
