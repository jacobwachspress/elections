# -*- coding: utf-8 -*-
"""
Created on Tue Jun 16 10:56:55 2020

@author: Jacob
"""

import pandas as pd
import urllib.request
import zipfile
import os
import shutil
import geopandas as gpd
import tempfile

## SCRIPTS FOR DOWNLOADING CENSUS DATA ##

def zipped_shapefile_to_geo_df(file_URL):
    ''' Downloads a zipped shapefile and turns it into a GeoDataFrame.
    
    Arguments: 
        file_URL: url of zipped shapefile, containing exactly one .shp file
        
    Output:
        GeoDataFrame corresponding to the shapefile in the zip folder '''
    
    # set temporary directory to download zip file
    tempfile.TemporaryDirectory()
    output_path = tempfile.gettempdir() + '/temp'
    if not os.path.isdir(output_path):
        os.mkdir(output_path)

    # read in file to temporary directory
    file_loc = output_path + '/temp.zip'
    urllib.request.urlretrieve(file_URL, file_loc)
    urllib.request.urlcleanup()

    # unzip file
    zip_ref = zipfile.ZipFile(file_loc, 'r')
    zip_ref.extractall(output_path)
    zip_ref.close()
    
    # delete cpg due to potential encoding error
    for file in os.listdir(output_path):
        if file[-4:] == '.cpg':
            os.remove(output_path + '/' + file)
    
    # find all files ending in .shp
    shapefiles = [file for file in os.listdir(output_path) if \
                  file[-4:] == '.shp']
    
    # check that there is exactly 1 such file (exception if not)
    if (len(shapefiles) != 1):
        shutil.rmtree(output_path)
        raise Exception("Not exactly one shapefile in zip folder. See  " + \
                        str(output_path))
    
    # generate GeoDataFrame from shapefile
    shp = shapefiles[0]
    geo_df = gpd.read_file(output_path + '/' + shp)
    
    # remove temporary folder
    shutil.rmtree(output_path)
    
    # return GeoDataFrame
    return geo_df

def download_state_leg_geo_df(state_fips, year, chamber='U', df_index='GEOID'):
    ''' Downloads the shapefile of state legislature boundaries and returns
    a GeoDataFrame.
    
    Arguments:
        state_fips: 2-character string corresponding to a state's FIPS code
        year: string denoting the year for which we want the boundaries
        chamber: 'U' for upper, 'L' for lower
        df_index: column we want for the index of the DataFrame
    
    Output: GeoDataFrame of desired boundaries, indexed by df_index '''
    
    # download shapefile
    file_path = 'https://www2.census.gov/geo/tiger/TIGER' + str(year) + '/'
    abbrev = 'SLD' + chamber
    full_path = file_path + abbrev.upper() + '/tl_' + str(year) + '_' + \
                        state_fips + '_' +  abbrev.lower() + '.zip'
    
    # get GeoDataFrame from shapefile, set index                    
    geo_df = zipped_shapefile_to_geo_df(full_path)
    geo_df.set_index(df_index, inplace=True)
    
    return geo_df
    
def find_land_area(geo_df, geo_id, area='ALAND'):
    return geo_df.loc[geo_id, area]

def find_population(state_fips, geoid, year, chamber='U'):
    return