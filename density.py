# -*- coding: utf-8 -*-
"""
Created on Thu Jul 16 16:09:04 2020

@author: Jacob
"""
import urllib
import zipfile
import tempfile
import os
import shutil
import requests
import pandas as pd
import geopandas as gpd
import numpy as np
import geo_helper.helper_tools.file_management as fm
import geo_helper.helper_tools.areal_interpolation as areal


def main():
    # set parameters
    census_vars = {'H001001': 'housing', 'H010001': 'pop', 'GEO_ID': 'GEOID10'}
    density_path = 'data/output/density/'

    # set output path for block groups data
    output_path = density_path + 'block_groups/'
    if not os.path.isdir(output_path):
        os.mkdir(output_path)
    url_start = 'https://www2.census.gov/geo/tiger/TIGER2010/BG/2010/tl_2010_'
    url_end = '_bg10.zip'

    # get all fips
    fips_df = pd.read_csv('data/input/general/state_fips.csv')
    all_fips = fips_df['fips'].astype(str).str.zfill(2).unique()

    # generate shapefiles
    for st_fips in all_fips:
        process_state_census_data(st_fips, census_vars, output_path, url_start,
                                  url_end)

    # add key colums and save to clean folder
    for st_fips in all_fips:
        # get file name
        file = st_fips + '_block_group.shp'
        # grab geo_df
        geo_df = gpd.read_file(density_path + 'block_groups/' + file)
        # fix area column, square meters to square miles
        geo_df['area'] = (geo_df['ALAND10']+geo_df['AWATER10']) / 2589988
        # add density columns
        geo_df = get_densities(geo_df)
        # write shapefile
        output_path = density_path + 'block_groups/'
        fm.save_shapefile(geo_df, output_path + file)

    # areal interpolation
    for st_fips in all_fips:

        # get file name
        file = st_fips + '_block_group.shp'

        # get block group geo_df
        bg_path = density_path + 'block_groups/'
        bg_df = gpd.read_file(bg_path + file)
        bg_df['pop'] = bg_df['pop'].astype(int)

        # for upper and lower
        for cham in ['upper', 'lower']:

            # get the target geo_df file
            dist_file = 'data/input/foundation/shp/' + cham + '/tl_2019_'
            dist_file += st_fips + '_sld' + cham[0] + '.shp'

            # if the file exists
            if os.path.exists(dist_file):
                dist_df = gpd.read_file(dist_file)

                # specify columns for aggregation and block group id
                s_cols = ['density_0', 'density_1', 'density_2', 'density_3',
                          'pop']
                t_cols = ['GEOID', 'NAMELSAD']

                # areal interpolation
                _, out_dist_df = areal.aggregate(bg_df, dist_df,
                                                         source_columns=s_cols,
                                                         target_columns=t_cols)

                # rename some columns
                dist_cols = {'density_0': 'rural', 'density_1': 'exurban',
                             'density_2': 'suburban', 'density_3': 'urban'}

                out_dist_df = out_dist_df.rename(columns=dist_cols)

                # prepare output paths to write shapefiles
                dist_output_path = density_path + cham + '/'
                if not os.path.isdir(dist_output_path):
                    os.mkdir(dist_output_path)

                fm.save_shapefile(out_dist_df, dist_output_path + st_fips +
                                  '_districts.shp')


def get_census_data(variables, st_fips, level='block group'):
    ''' Downloads census data from 2010 Census Summary File for a given
    state at a given geographic level.

    Arguments:
        variables: dictionary of data points to download for each geography,
            keyed by census code for the variable and values given by the
            corresponding  name we would like for the variable
            (see: https://api.census.gov/data/2010/dec/sf1/variables.html)
        st_fips: two-digit string that gives the state fips code for the
            download (sadly all at once is not allowed)
        level: smallest geography to grab the data (options: state, county,
            tract, block group, block)

    Output: pandas dataframe with all desired variables as columns, rows
        broken down by level
    '''

    # start of API web address
    api_path = 'https://api.census.gov/data/2010/dec/sf1?get='

    # bulid the string for the variables in the web address
    vars_string = ','.join(variables.keys())

    # build the string for the geographic level of download
    level_string = '&for=' + level + ':*'

    # build the geographic hierachy to allow a search at this level
    hierarchy_string = ''
    for higher_level in ['state', 'county', 'tract']:

        # if this is not our level of search
        if level != higher_level:

            # add to the hierarchy in the proper format for web search
            hierarchy_string = hierarchy_string + '&in=' + higher_level + ':'

            # add st_fips if needed, add wildcard for other levels
            if higher_level == 'state':
                hierarchy_string = hierarchy_string + st_fips
            else:
                hierarchy_string = hierarchy_string + '*'

    # get URL for API query
    query_url = api_path + vars_string + level_string + hierarchy_string

    # read in url as json
    data = requests.get(query_url).json()

    # convert to DataFrame
    df = pd.DataFrame(data[1:], columns=data[0])

    # rename columns
    df = df.rename(columns=variables)

    return df


def merge_geo_and_data(st_fips, geo_df, variables, level='block group'):
    ''' Given a GeoDataFrame, queries census for additional info for each
    record and merges into a new GeoDataFrame.

    Arguments:
        st_fips: two-digit string, state FIPS code
        geo_df: GeoDataFrame with at least the following columns:
            geometry, GEOID10
        variables: dictionary of data points to dowload for each geography,
            keyed by census code for the variable and values given by the
            corresponding  name we would like for the variable
            (see: https://api.census.gov/data/2010/dec/sf1/variables.html)
        level: geography level at which geo_df is broken down

    Output: geo_df with desired columns merged in
    '''

    # add geo_id column to variables, will be needed for merge
    d = variables.copy()
    d['GEO_ID'] = 'GEOID10'

    # get census data
    census_df = get_census_data(d, st_fips, level)

    # fix geoid in census data, which pops out with extraneous characters
    # (ex. 1000000US250010101001000)
    census_df['GEOID10'] = census_df['GEOID10'].apply(lambda x:
                                                      x[x.index('S') + 1:])

    # merge dataframes
    return pd.merge(geo_df, census_df, how='left', on='GEOID10')


def zipped_shapefile_to_geo_df(file_URL):
    ''' Downloads zipped shapefile and turns it into a GeoDataFrame

    Arguments:
        file_URL: url of zipped shapefile

    Output:
        GeoDataFrame corresponding to the shapefile in the zip folder
        (assumption is that there is just one .shp file)
    '''

    # set temporary directory to download zip file
    tempfile.TemporaryDirectory()
    output_path = tempfile.gettempdir() + '/temp'
    if not os.path.isdir(output_path):
        os.mkdir(output_path)

    # read in file
    file_loc = output_path + '/temp.zip'
    urllib.request.urlretrieve(file_URL, file_loc)
    urllib.request.urlcleanup()

    # unzip
    zip_ref = zipfile.ZipFile(file_loc, 'r')
    zip_ref.extractall(output_path)
    zip_ref.close()

    # delete cpg, which can cause an error
    for file in os.listdir(output_path):
        if file[-4:] == '.cpg':
            os.remove(output_path + '/' + file)

    # get all .shp files in zip folder
    shapefiles = [file for file in os.listdir(output_path) if
                  file[-4:] == '.shp']

    # if there is not exactly one .shp file
    if (len(shapefiles) != 1):
        shutil.rmtree(output_path)
        raise Exception("Not exactly one shapefile in zip folder. See  " +
                        str(output_path))

    # turn the shapefile to a GeoDataFrame
    shp = shapefiles[0]
    geo_df = gpd.read_file(output_path + '/' + shp)

    # remove temporary folder
    shutil.rmtree(output_path)

    return geo_df


def download_geos(st_fips, url_start, url_end):
    ''' Downloads the (block group) geographies for a state from the census FTP.

    Arguments:
        st_fips: two-digit string, state FIPS code
        url_start: part of census download website before st_fips
        url_end: part of census download website after st_fips

    Output: geo_df with desired geographies
    '''

    # get url to download from census
    url = url_start + st_fips + url_end

    # get geo_df
    return zipped_shapefile_to_geo_df(url)


def process_state_census_data(st_fips, census_vars, output_path,
                              geo_url_start, geo_url_end, level='block group',
                              cols_to_keep=False):
    ''' Generates a shapefile of geographies with all the necessary fields
    for density processing.

    Arguments:
        st_fips: two-digit string, state FIPS code
        census_vars: dict of census data fields to store for each geography,
            keyed by census code for the fields and values given by the
            corresponding name we would like for the field
        output_path: folder to write the results
        geo_url_start, geo_url_end: pieces of url for download of geographies
            (takes the form geo_url_start + st_fips + geo_url_end)
        level: level of census geography for analysis

    Output: none (shapefile is written)
    '''

    # create folder for shapefile if needed
    if not os.path.isdir(output_path):
        os.mkdir(output_path)

    # read in geographies
    geo_df = download_geos(st_fips, geo_url_start, geo_url_end)

    # read in and merge census data
    merged_df = merge_geo_and_data(st_fips, geo_df, census_vars, level)

    # drop unnecessary columns
    if cols_to_keep:
        merged_df = merged_df[cols_to_keep + list(census_vars.values())]

    # write to shapefile
    out_file = '_'.join([st_fips] + level.split(' '))
    fm.save_shapefile(merged_df, output_path + out_file + '.shp')

    return


def get_categories(density):
    ''' Given the density of a region (households / square mile), classify
    the region into one of four density categories. Give 0-to-1 weights for
    all four possiblities.

    Arguments:
        density: float, households /sq mile

    Output:
        numpy array, elements summing to 1, indicating the weight
            of each density category (sometimes more than 1 non-zero weight
            due to smoothing near the boundary)
    '''

    # set density bounds for different categories, based on Jed Kolko research
    # 5000 is not an upper bound, but used later in code to see if we were
    # "close" (relatively) to a boundary between intervals
    densities = np.asarray([0, 102, 800, 2213, 5000])

    # initialize output arroy
    output = np.zeros(4)

    # find the index of the lower bound where this density fits
    ix = (np.where(densities <= density)[0])[-1]

    # if we are not in the highest (artificial) range
    if ix != 4:

        # check if we are within 10 percent of a boundary
        pctile = (density - densities[ix]) / (densities[ix+1] - densities[ix])

        # if we are on the low end
        if pctile <= 0.1:
            # add in some weight to the lower category
            if ix != 0:
                output[ix-1] = (0.1-pctile)*5

        # if we are on the high end
        if pctile >= 0.9:
            # add in some weight to the higher category
            if ix != len(densities) - 2:
                output[ix+1] = (pctile-0.9)*5

    # if we are in the artificial highest range, fix the index
    else:
        ix = 3

    # set weight of main index
    output[ix] = 1 - np.sum(output)

    # return np array of the values
    return output


def get_densities(df, area_col='area', housing_col='housing', pop_col='pop'):

    # for each record
    for i, region in df.iterrows():

        # deal with water only districts
        if float(region[area_col]) == 0:
            df.loc[i, 'water_people'] = float(region[pop_col])

        else:
            # get housing units per square mile
            density = float(region[housing_col]) / float(region[area_col])

            # get density categories
            category_weights = get_categories(density)

            # get people in each category
            people = category_weights * float(region[pop_col])

            # for each element of people
            for j in range(len(people)):

                # update df for density field
                df.loc[i, 'density_' + str(j)] = people[j]

    return df


if __name__ == "__main__":
    main()
