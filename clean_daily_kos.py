# -*- coding: utf-8 -*-
"""
Created on Thu Jul 16 09:28:26 2020

@author: Jacob
"""

import numpy as np
import pandas as pd
from functools import reduce
import os

def main():

    # get input and output folders for election data
    money_path = "G:/Shared drives/princeton_gerrymandering_project/Moneyball/"
    input_path = money_path + "state/historical_election_results/"
    output_path = money_path +\
            "foundation\\raw\\pres_results_by_state_leg_district\\"
    
    # make the output folder if neded
    if not os.path.isdir(output_path):
        os.mkdir(output_path)
    
    # for each file in the input folder
    for file in os.listdir(input_path):
        
        # read in csv to dataframs
        df = pd.read_csv(input_path+file)
        
        # if there are empty rows
        if any(df.isnull().all(axis=1)):
            
            # find the first empty row
            first_empty_row = list(df.isnull().all(axis=1)).index(True)
            
            # drop all empty rows and the last full row, which is "TOTAL"
            to_drop = [i for i in range(len(df)) if i >= first_empty_row -1]
            df = df.drop(to_drop)
        
        # otherwise, just drop the last full row, which is "TOTAL"
        else:
            df = df.drop(len(df)-1)
            
        # create district and state columns
        df['DISTRICT'] = df[df.columns[0]].apply(lambda x: df.columns[0] + \
                                                      ' ' + str(x))
        df['STATE'] = df.columns[0][0:2]
        
        # establish races of concern
        races_to_keep = ['2016 President', '2012 President', '2014 Senate', 
                         '2012 Senate']
        
        # find the indices of these races in df
        race_indices = [i for i in range(len(df.columns)) \
                                if df.columns[i] in races_to_keep]
        
        # keep these indices, and the one after, to get both election results
        indices_to_keep = [i for i in range(len(df.columns)) \
                                   if i in race_indices or i-1 in race_indices]
        
        # find the columns to keep, and trim dataframe
        cols_to_keep = [df.columns[i] for i in indices_to_keep] 
        df1 = df[cols_to_keep+['DISTRICT', 'STATE']].copy()
        
        # rename columns
        new_names = {}
        for ix in race_indices:
            col = df.columns[ix]
            new_names[col] = df1.loc[0, col] + ' ' + col + ' D'
            new_names[df.columns[ix+1]] = df1.loc[0, df.columns[ix+1]] + ' ' \
                                                        + col + ' R'
        df1 = df1.rename(columns=new_names)
        
        # drop row listing candidate with no district
        df1 = df1.drop(0)
        
        # drop unnecessary columns
        df1 = df1[['STATE', 'DISTRICT']+list(new_names.values())]
        
        # add _Upper to file names without chamber specified (manually checked--
        # this is right)
        if '_' not in file:
            file = file[:-4] + '_Upper.csv'
        df1.to_csv(output_path + file, index=False)
    
if __name__ == "__main__":
   main()