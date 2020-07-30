"""Get SLDU and SLDL for the entire country with distributed labels."""

import pandas as pd
import geopandas as gpd
from geo_helper.helper_tools import file_management as fm
from geo_helper import edit_shapefiles as es
import os


def main():
    money_path = 'G:/Shared drives/princeton_gerrymandering_project/Moneyball'
    money_path += '/foundation/'

    # Get Congressional Shapefile
    print('Creating Congressional Districts')
    path = money_path + 'shp/congressional/tl_2019_us_cd116.shp'
    df_congress = fm.load_shapefile(path)
    df_fips = pd.read_csv(money_path + 'raw/state_fips.csv')
    df_fips['fips'] = df_fips['fips'].astype(str).str.zfill(2)
    df_congress = df_congress.merge(df_fips, left_on='STATEFP',
                                    right_on='fips')

    # Create nationwide file for upper chamber districts
    print('Creating Upper Chambers')
    # Get all shapefiles in directory
    upper_files = os.listdir(money_path + 'shp/upper')
    upper_shp = [x for x in upper_files if x[-4:] == '.shp']

    # Initialize upper chamber dataframe
    df_upper = pd.DataFrame()

    # Iterate through each shapefile and append to df_upper
    for file in upper_shp:
        path = money_path + 'shp/upper/' + file
        df_current = fm.load_shapefile(path)
        df_upper = df_upper.append(df_current)

    # Make df_upper a geopandas dataframe
    df_upper = gpd.GeoDataFrame(df_upper, geometry='geometry')

    # Only keep state
    df_upper = df_upper.merge(df_fips, left_on='STATEFP', right_on='fips')

    # Save into national folder
    path = money_path + 'shp/national/upper_chambers.shp'
    fm.save_shapefile(df_upper, path)

    # Create nationwide file for lower chamber districts
    print('Creating Lower Chambers')
    # Get all shapefiles in directory
    lower_files = os.listdir(money_path + 'shp/lower')
    lower_shp = [x for x in lower_files if x[-4:] == '.shp']

    # Initialize lower chamber dataframe
    df_lower = pd.DataFrame()

    # Iterate through each shapefile and append to df_lower
    for file in lower_shp:
        path = money_path + 'shp/lower/' + file
        df_current = fm.load_shapefile(path)
        df_lower = df_lower.append(df_current)

    # Make df_lower a geopandas dataframe
    df_lower = gpd.GeoDataFrame(df_lower, geometry='geometry')

    # Only keep state
    df_lower = df_lower.merge(df_fips, left_on='STATEFP', right_on='fips')

    # Save into national folder
    path = money_path + 'shp/national/lower_chambers.shp'
    fm.save_shapefile(df_lower, path)

    # Distribute congressional geoid to upper chamber districts
    print('Distributing Upper Chamber')
    congress_cols = ['GEOID']
    upper_cols = ['cd_geoid']
    path = money_path + 'shp/national/upper_chambers_labels.shp'
    df_upper_label = es.distribute_label(df_congress, congress_cols, df_upper,
                                         upper_cols, progress=100,
                                         debug_col='GEOID')
    fm.save_shapefile(df_upper_label, path)

    # distribute congressional and SLDU geoid to lower chamber districts
    print('Distributing Lower Chamber')
    congress_cols = ['cd_geoid', 'GEOID']
    lower_cols = ['cd_geoid', 'sldu_geoid']
    path = money_path + 'shp/national/lower_chambers_labels.shp'
    df_lower_label = es.distribute_label(df_upper_label, congress_cols,
                                         df_lower, lower_cols, progress=100,
                                         debug_col='GEOID')
    fm.save_shapefile(df_lower_label, path)

    # Turn upper chambers from a geodataframe to a regular dataframe
    df_upp = pd.DataFrame(df_upper_label)

    # Create better names for columns we will keep
    df_upp['state_fips'] = df_upp['STATEFP']
    df_upp['geoid'] = df_upp['GEOID']
    df_upp['district_num'] = df_upp['geoid'].apply(lambda x: x[-3:])
    df_upp['name'] = df_upp['NAMELSAD']

    # Keep and Sort Columns
    keep_cols = ['state', 'state_fips', 'cd_geoid', 'geoid', 'district_num',
                 'name']
    df_upp = df_upp[keep_cols]

    # Save
    df_upp.to_csv(money_path + 'clean/sldu_labels.csv', index=False)

    # Turn upper chambers from a geodataframe to a regular dataframe
    df_low = pd.DataFrame(df_lower_label)

    # Create better names for columns we will keep
    df_low['state_fips'] = df_low['STATEFP']
    df_low['geoid'] = df_low['GEOID']
    df_low['district_num'] = df_low['geoid'].apply(lambda x: x[-3:])
    df_low['name'] = df_low['NAMELSAD']

    # Keep and Sort Columns
    keep_cols = ['state', 'state_fips', 'cd_geoid', 'sldu_geoid', 'geoid',
                 'district_num', 'name']
    df_low = df_low[keep_cols]

    # Save
    df_low.to_csv(money_path + 'clean/sldl_labels.csv', index=False)
    return


if __name__ == "__main__":
    main()
