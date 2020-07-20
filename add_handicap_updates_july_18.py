"""Add July 18th updates from Chaz."""
import pandas as pd

def main():
    # Load original Chaz data and updates
    money_path = 'G:/Shared drives/princeton_gerrymandering_project/Moneyball/'
    df_lower_old = pd.read_csv(money_path + 'state/state_assembly.csv')
    df_upper_old = pd.read_csv(money_path + 'state/state_senate.csv')
    df = pd.read_csv(money_path + 'chaz/chaz_updates_07_18.csv')

    # Convert rating to title case
    df['NEW_RATING'] = df['NEW_RATING'].apply(lambda x: tc.titlecase(x))

    # Add hyphen to district
    df['DISTRICT'] = df['DISTRICT'].apply(lambda x: '-'.join(x.split()))
    df_lower = df[df['DISTRICT'].str.contains('HD')]
    df_upper = df[df['DISTRICT'].str.contains('SD')]

    # Join updates
    df_lower = df_lower.merge(df_lower_old, how='right')
    df_upper = df_upper.merge(df_upper_old, how='right')

    # Make new ratings the ratings
    df_lower['RATING'] = df_lower['NEW_RATING'].fillna(df_lower['RATING'])
    df_upper['RATING'] = df_upper['NEW_RATING'].fillna(df_upper['RATING'])

    # Drop the new rating
    df_lower = df_lower.drop('NEW_RATING', axis=1)
    df_upper = df_upper.drop('NEW_RATING', axis=1)

    # Rename original handicap data so we have a record of the date
    df_lower_old.to_csv(money_path + 'chaz/chaz_lower_chamber_07_01.csv',
                        index=False)
    df_upper_old.to_csv(money_path + 'chaz/chaz_upper_chamber_07_01.csv',
                        index=False)

    # Save Chaz data with updates
    df_lower.to_csv(money_path + 'chaz/chaz_lower_chamber_07_18.csv',
                    index=False)
    df_upper.to_csv(money_path + 'chaz/chaz_upper_chamber_07_18.csv',
                    index=False)
