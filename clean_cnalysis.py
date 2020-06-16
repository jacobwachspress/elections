"""Clean Chaz Nuttycombe's spreadsheets for moneyball analysis."""
import pandas as pd


def get_incumb(d, r, i):
    """Determine the party of the incumbent if there is one.

    Arguments:
        d, r, and i are booleans of whether there is an incubment of
        that party
    """
    if d:
        return 'D'
    elif r:
        return 'R'
    elif i:
        return 'I'
    else:
        return False


def clean(in_path, out_path):
    """Preprocessing for moneyball

    Put ratings into cleaner format. We end up with the following attributes:
        state, state_fips, district, district_num, incumbent, flip, favored,
        confidence, nom_R, nom_D, nom_I

    If there is no incumbent entry is False
    If race is a toss-up favored is False

    Arguments:
        in_path: path to csv of chaz's spreadsheet to process
        out_path: path to save cleaned dataframe
    """
    # Load dataframe
    df = pd.read_csv(in_path)

    # Extract if we expect a change and which party is favored
    df['flip'] = df['FLIP'].notna()
    df['favored'] = df['RATING'].apply(lambda x: x.split(' ')[-1])
    df['favored'] = df['favored'].apply(lambda x: False if x == 'Toss-Up'
                                        else x)
    df['confidence'] = df['RATING'].apply(lambda x: x.split(' ')[0])

    # Remove states with multi-member districts
    df = df[~df['STATE'].isin(['VT', 'WV'])]

    # Get if there is an incumbent
    df['incub_D'] = df['D NOM'].str.contains('[I]').fillna(False)
    df['incub_R'] = df['R NOM'].str.contains('[I]').fillna(False)
    df['incub_I'] = df['I NOM'].str.contains('[I]').fillna(False)

    # Get which incumbent
    df['incumbent'] = df.apply(lambda r: get_incumb(r['incub_D'], r['incub_R'],
                                                    r['incub_I']), axis=1)
    df = df.drop(columns=['incub_D', 'incub_R', 'incub_I'])

    # Get state and district as lowercase as well as nominees
    df['state'] = df['STATE']
    df['district'] = df['DISTRICT']
    df['nom_R'] = df['R NOM'].fillna(False)
    df['nom_D'] = df['D NOM'].fillna(False)
    df['nom_I'] = df['I NOM'].fillna(False)
    df['nom_R'] = df['nom_R'].apply(lambda x: False if not x else
                                    x.split(' [I]')[0])
    df['nom_D'] = df['nom_D'].apply(lambda x: False if not x else
                                    x.split(' [I]')[0])
    df['nom_I'] = df['nom_I'].apply(lambda x: False if not x else
                                    x.split(' [I]')[0])

    # lowercase geoid
    df['geoid'] = df['GEOID'].str.zfill(5)
    df['state_fips'] = df['geoid'].apply(lambda x: x[:2])
    df['district_num'] = df['geoid'].apply(lambda x: x[2:])

    # Get relevant columns
    keep_cols = ['state', 'state_fips', 'district', 'district_num',
                 'incumbent', 'flip', 'favored', 'confidence', 'nom_R',
                 'nom_D', 'nom_I']
    df = df[keep_cols]

    # Save dataframe
    df.to_csv(out_path, index=False)
    return
