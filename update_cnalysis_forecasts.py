"""Apply updates from CNalysis."""
import pandas as pd
import titlecase as tc


def main():
    """Load original cnalysis data and apply updates"""
    # Define path
    input_path = 'data/input/CNalysis/'
    output_path = 'data/output/CNalysis/'

    # Load original data
    lower_old_path = input_path + 'ratings_lower_chamber_original.csv'
    upper_old_path = input_path + 'ratings_upper_chamber_original.csv'
    df_lower_old = pd.read_csv(lower_old_path).dropna(subset=['RATING'])
    df_upper_old = pd.read_csv(upper_old_path).dropna(subset=['RATING'])

    # Define update date
    update_date = '10_06'

    # Define update paths. Add in reverse date order b/c we'll drop duplicates
    
    update_paths = []
    update_paths.append(input_path + 'nebraska_updates.csv')

    # Load updates
    df = pd.DataFrame()
    for update_path in update_paths:
        df_update = pd.read_csv(update_path).dropna()
        df = df.append(df_update)

    # Drop duplicate updates. Assume updates are in reverse date order
    df = df.drop_duplicates(subset=['DISTRICT'])

    # sometimes he calls HD districts AD districts
    df['DISTRICT'] = df['DISTRICT'].apply(lambda x: x.replace('AD', 'HD'))

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

    # Save updated predictions with update date and as most recent
    lower_path = output_path + 'ratings_lower_chamber_'
    upper_path = output_path + 'ratings_upper_chamber_'
    df_lower.to_csv(lower_path + update_date + '.csv', index=False)
    df_upper.to_csv(upper_path + update_date + '.csv', index=False)
    df_lower.to_csv(lower_path + 'most_recent.csv', index=False)
    df_upper.to_csv(upper_path + 'most_recent.csv', index=False)
    return


if __name__ == "__main__":
    main()
