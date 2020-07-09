"""
Helper methods to make changes to shapefiles
"""

import geopandas as gpd
import pandas as pd
import shapely as shp


def dissolve(df, dissolve_attribute):
    ''' Dissolves boundaries according to the dissolve_attribute (diss_att)

    Arguments:
        in_path:
            geodataframe of shapefile to dissolve

        dissolve_attribute:
            attribute to dissolve boundaries according to

    Output:
        Shapefile with the boundaries dissolved

    Additional:
        Main use is to generate a precinct level shapefile from census block
        data
    '''
    # Get unique values of dissolved attribute
    dissolve_names = list(df[dissolve_attribute].unique())

    # Create dataframe for dissolved shapefile
    df_dissolve = pd.DataFrame(columns=[dissolve_attribute, 'geometry'])

    # Iterate through each unique element in the dissolve_attribute column
    for i, elem in enumerate(dissolve_names):
        if (i + 1) % 100 == 0:
            print(str(i + 1) + '/' + str(len(dissolve_names)))
        # Use cascaded union to combine all smaller geometries with the same
        # dissolve attribute
        df_poly = df[df[dissolve_attribute] == elem]
        polys = list(df_poly['geometry'])
        geometry = shp.ops.cascaded_union(polys)

        # Add the union to the new dataframe
        df_dissolve.at[i, 'geometry'] = geometry
        df_dissolve.at[i, dissolve_attribute] = elem

    return gpd.GeoDataFrame(df_dissolve, geometry='geometry')
