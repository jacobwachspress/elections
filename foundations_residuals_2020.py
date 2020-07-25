"""Get residuals between chaz predictions and foundations predictions.

Key chambers are:
    TX Lower
    KS Lower
    NC Lower
    FL Lower
    KS Upper
    NC Upper
    MN Upper
"""

import pandas as pd
from foundations_blending_2018 import chaz_share


def main():
    money_path = 'G:/Shared drives/princeton_gerrymandering_project/Moneyball/'
    path = money_path + 'foundation/clean/'

    # Load input data and clean
    df = pd.read_csv(money_path + 'state/all_input_data.csv')
    df['district_num'] = df['district_num'].astype(str).str.zfill(3)
    df['chamber'] = df['office']

    # Remove all uncontested races
    df = df[df['confidence'] != 'Uncontested']

    # Get the voteshare according to chaz
    df['chaz_share'] = df.apply(lambda r: chaz_share(r['favored'],
                                                     r['confidence']), axis=1)

    # Keep relevant columns
    keep_cols = ['state', 'district_num', 'chamber', 'confidence',
                 'chaz_share']
    df = df[keep_cols]

    # Load foundations data and clean
    df_found = pd.read_csv(path + 'foundations_predictions_2020.csv')
    df_found['district_num'] = df_found['district_num'].astype(str)
    df_found['district_num'] = df_found['district_num'].str.zfill(3)
    keep_cols = ['state', 'district_num', 'chamber', 'found_share']
    df_found = df_found[keep_cols]

    # Merge, get residual, and save
    df = df.merge(df_found)
    df['residual'] = df['chaz_share'] - df['found_share']
    df.to_csv(path + 'foundations_residuals_2020.csv', index=False)
    return


if __name__ == "__main__":
    main()
