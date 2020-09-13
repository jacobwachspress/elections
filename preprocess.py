"""Preprocessing all relevant input data

We run the main functions of other files in the correct order.

This must be run before redistricting_moneyball.py
"""

import cnalysis_input_components
import density
import district_areal_interpolation
import economist_forecasts
import incumbency_2016_and_2018
import foundations_input_components
import foundations_prediction_2020
import update_cnalysis_forecasts
import wikipedia_lower_chamber_incumbency
import wikipedia_upper_chamber_incumbency


def preprocess(wikipedia_scrape=True, economist_scrape=True,
               find_density=True, interpolate_districts=True,
               regenerate_CNalysis_ratings=True, district_input_data=True,
               foundations=True):
    """Execute Preprocessing."""
    # get updated CNalysis ratings
    if regenerate_CNalysis_ratings:
        print('regenerating CNalysis ratings')
        update_cnalysis_forecasts.main()

    # get incumbents (important to know who holds seats where there is
    # no election and therefore no CNalysis rating)
    if wikipedia_scrape:
        print('getting incumbency data for no-election districts')
        wikipedia_lower_chamber_incumbency.main()
        wikipedia_upper_chamber_incumbency.main()

    # calculate the urban/suburban/exurban/rural breakdown of the districts
    # this takes some time
    if find_density:
        print('calculating urban/suburban/exurban/rural breakdown ' +
              'of the districts using census data')
        # density.main()

    # merge needed district-specific data to CNalysis ratings
    if district_input_data:
        print('assembling needed district-specific data')
        cnalysis_input_components.main()

    # foundations model input
    if foundations:

        # get all district input components
        if interpolate_districts:
            print('using areal interpolation to help estimate ' +
                  'historical presidential results where data is missing')
            district_areal_interpolation.main()

        print('assembling needed district-specific data for foundations')
        foundations_input_components.main()

        # get predictions
        if economist_scrape:
            print('getting expected presidential margins from Economist')
            economist_forecasts.main()
        print('merging old incumbency data for foundations')
        incumbency_2016_and_2018.main()
        print('finding foundations predicted margins')
        foundations_prediction_2020.main()
    return


if __name__ == "__main__":
    preprocess()
