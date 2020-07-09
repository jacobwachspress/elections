import geo_helper.helper_tools.file_management as fm
import numpy as np
import pandas as pd


def distribute_label(df_large, large_cols, df_small, small_cols=False,
                     small_path=False, progress=False, debug_col=False):
    ''' Take labels from a shapefile that has larger boundaries and interpolate
    said labels to shapefile with smaller boundaries. By smaller boundaries we
    just mean more fine geographic boundaries. (i.e. census blocks are smaller
    than counties)

    We use the greatest area method. However, when no intersection occurs, we
    simply use the nearest centroid.

    NOTE: By default interpolates a string type because it is a label

    Arguments:

        df_large:
            larger shapefile giving the labels

        large_cols:
            LIST of attributes from larger shp to interpolate to
            smaller shp

        df_small:
            smaller shapefile receiving the labels

        small_cols:
            LIST of names for attributes given by larger columns.
            Default will be False, which means to use the same attribute names

        small_path:
            path to save the new dataframe to

        progress:
            how often to print

        debug_col:
            column in df_small to print out when error occurs.
            usually block_id or geoid

    Output:
        edited df_small dataframe
    '''

    # handle default for small_cols
    if small_cols is False:
        small_cols = large_cols

    # Check that large and small cols have same number of attributes
    if len(small_cols) != len(large_cols):
        return False

    if not set(large_cols).issubset(set(df_large.columns)):
        return False

    # Let the index by an integer for spatial indexing purposes
    df_large.index = df_large.index.astype(int)

    # Drop small_cols in small shp if they already exists
    drop_cols = set(small_cols).intersection(set(df_small.columns))
    df_small = df_small.drop(columns=drop_cols)

    # Initialize new series in small shp
    for col in small_cols:
        df_small[col] = pd.Series(dtype=object)

    # construct r-tree spatial index
    si = df_large.sindex

    # Get centroid for each geometry in the large shapefile
    df_large['centroid'] = df_large['geometry'].centroid

    # Find appropriate matching large geometry for each small geometry
    df_small = df_small.reset_index(drop=True)
    for ix, row in df_small.iterrows():
        try:
            if progress:
                if (ix + 1) % progress == 0:
                    print('\t' + str(ix + 1) + '/' + str(len(df_small)))
            # Get potential matches
            small_poly = row['geometry']
            potential_matches = [df_large.index[i] for i in
                                 list(si.intersection(small_poly.bounds))]

            # Only keep matches that have intersections
            matches = [m for m in potential_matches
                       if df_large.at[m, 'geometry'].intersection(
                       small_poly).area > 0]

            # No intersections. Find nearest centroid
            if len(matches) == 0:
                small_centroid = small_poly.centroid
                dist_series = df_large['centroid'].apply(lambda x:
                                small_centroid.distance(x))
                large_ix = dist_series.idxmin()

            # One intersection. Only one match
            elif len(matches) == 1:
                large_ix = matches[0]

            # Multiple intersections. compare fractional area
            # of intersection
            else:
                area_df = df_large.loc[matches, :]
                area_series = area_df['geometry'].apply(lambda x:
                                x.intersection(small_poly).area
                                / small_poly.area)
                large_ix = area_series.idxmax()

            # Update values for the small geometry
            for j, col in enumerate(large_cols):
                df_small.at[ix, small_cols[j]] = df_large.at[large_ix, col]
        except:
            print('---------------------\n')
            error_block = str(row['block_id']) + ' - ' + str(ix + 1)
            error_block += '/' + str(len(df_small))
            print(error_block)
            print('\n-------------------')

    # Save and return the updated small dataframe
    if small_path:
        fm.save_shapefile(df_small, small_path)
    return df_small


def distribute_values(df_source, source_cols, df_target, reference_col,
                      distribute_col):
    '''
    Distribute attribute values of source geometries into the target geometries

    Both dataframes need to have a connecting reference column. This can be
    provided after running distribute labels.

    The reference column is the grouping column. For example the source would
    have precinct election results and the targets would be census blocks
    that have already been assigned to precincts.

    Arguments:
        df_source:
            source shapefile providing the values to distribute

        source_cols:
            LIST of names of attributes in df_source to distribute

        df_target:
            target shapefile receiving values being distributed

        reference_col:
            column (id) that connects elements in the target and source
            dataframes (e.g. block group or precinct)

        distribute_col:
            column to determine how much of a value to distribute. Usuallly
            some form of population

    Output:
        edited df_target dataframe
    '''
    # Get an aggregated value of the distributed column in order to get a
    # distribution ratio. E.g. get total population of each precinct
    df_target_agg = df_target[[reference_col, distribute_col]]
    df_target_agg = df_target_agg.groupby(reference_col)
    df_target_agg = df_target_agg.aggregate(['sum'])
    df_target_agg.columns = df_target_agg.columns.droplevel()
    df_target_agg.columns = ['distribute_sum']

    # Merge aggregated values and get the distribute ratio
    df_target = df_target.merge(df_target_agg, left_on=reference_col,
                                right_index=True)
    df_target['distribute_ratio'] = df_target[distribute_col] / \
                                    df_target['distribute_sum']

    # Get the total value that needs to be distributed for each reference col
    df_source = df_source[source_cols + [reference_col]]
    df_source.columns = [x + '_total' for x in list(df_source.columns)]
    df_target = df_target.merge(df_source, left_on=reference_col,
                                right_on=reference_col+'_total')

    # Distribute values round to floor to not overestimate and save residue
    for col in source_cols:
        col_float = col + '_float'
        df_target[col_float] = df_target['distribute_ratio']
        df_target[col_float] *= df_target[col + '_total']
        df_target[col] = np.floor(df_target[col_float])
        df_target[col + '_decimal'] = df_target[col_float] - df_target[col]

    # Reset index. Iterate through preserving precinct totals
    df_target = df_target.reset_index(drop=True)
    for ix, row in df_source.iterrows():
        print(ix)
        if (ix + 1) % 100 == 0:
            print(str(ix + 1) + '/' + str(len(df_source)))
        # Get targets that have the same reference
        ref_total = reference_col + '_total'
        d_target = df_target[df_target[reference_col] == row[ref_total]]

        # Iterate through relevant columns
        for col in source_cols:
            target_sum = d_target[col].sum()
            actual_sum = row[col + '_total']

            # use all targets if no population but distribute values
            if d_target[distribute_col].sum() == 0:
                add_ixs = list(d_target.index)
                for add_ix in add_ixs:
                    df_target.at[add_ix, col] = 0
                add_ixs = add_ixs * 1000
            else:
                # Get order of target geometries to increment
                d_target = d_target[d_target[distribute_col] > 0]
                d_target = d_target.sort_values(by=col + '_decimal',
                                                ascending=False)

                # Increment target geometries
                # (* 1000 is just for safety in case we need to loop)
                add_ixs = list(d_target.index) * 1000
            for add_ix in range(int(actual_sum - target_sum)):
                df_target.at[add_ixs[add_ix], col] += 1

    # drop unnecessary columns
    drop_cols = []
    for col in source_cols:
        drop_cols.append(col + '_total')
        drop_cols.append(col + '_float')
        drop_cols.append(col + '_decimal')
    drop_cols += [reference_col + '_total', 'distribute_sum',
                  'distribute_ratio']

    df_target = df_target.drop(columns=drop_cols)
    return df_target
