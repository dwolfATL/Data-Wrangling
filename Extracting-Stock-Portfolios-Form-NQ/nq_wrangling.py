# -*- coding: utf-8 -*-
"""
Wrangling stock portfolio data from SEC Form N-Q on EDGAR
Author: DWolf

Source files can be downloaded through this R package: https://github.com/cran/edgar/tree/master/R
"""


import pandas as pd
import glob
import os
from datetime import datetime
from fuzzywuzzy import process

# List of CIKs (Central Index Keys) and company names
CIKs = pd.read_csv('CIKs.csv')

# List of all publicly traded companies on NASDAQ and NYSE
# Source: http://www.nasdaq.com/screening/company-list.aspx
companies = pd.read_csv('companylist.csv')

# Get a list of the first word of each company for matching purposes
companies['Company_firstword'] = companies['Name'].str.split().str.get(0)

# Used when identifying numeric columns
def check_int(x):
    try:
        return int(x)
    except ValueError:
        return False

# Applies fuzzywuzzy process function for fuzzy string matching
def fuzzy_match(company, companies):
    firstword = company.split()[0]
    potential_companies = list(companies[companies['Company_firstword'] == firstword]['Name'])
    return process.extractOne(company, potential_companies)[0]

file_path = 'filings_sample/'
filings = [os.path.basename(x) for x in glob.glob(file_path + '*.txt')]

# Loop through each file, parse it, identify Company and Share columns, and merge additional data
counter = 0
for filing in filings:
    
    # Allow continuation if error encountered
    try:
        # Track progress
        counter += 1
        print(str(counter) + ': ' + filing)
        
        # Read HTML and parse it into a single dataframe for each file
        file_data = pd.read_html(file_path + filing, flavor='bs4')
        df = pd.DataFrame(file_data[0])
        for i in range(1,len(file_data)):
            df = pd.concat([df,pd.DataFrame(file_data[i])])
        df.dropna(how='all', inplace=True) # drop rows that are entirely NA
        
        # Find which column has the company names by counting first word matches
        df_firstword = df.apply(lambda x: x.astype(str).str.split().str.get(0))
        company_col = df_firstword.isin(list(companies['Company_firstword'])).sum().idxmax()
        
        # Remove all rows that do not have a company name
        df['Company_firstword'] = df[company_col].str.split().str.get(0)
        df['match'] = df['Company_firstword'].isin(list(companies['Company_firstword']))
        df = df[df['match'] == True]
        df = df.drop('match', axis=1)
        
        # Find the Shares column by finding the column with the most numeric values
        df_num = df.applymap(lambda x: check_int(x))
        numeric_cols = df_num.sum().nonzero()
        shares_col = df.isnull().sum()[numeric_cols[0]].idxmin()
        df = df[df_num[shares_col] != False]
        
        df.rename(columns={company_col: 'Company'}, inplace=True)
        df.rename(columns={shares_col: 'Shares'}, inplace=True)
        
        # Add CIK, Fund name, Form type, Quarter, and File name, and reporting period to the data frame
        CIK = filing.split("_")[0]
        df['CIK'] = CIK
        df['Fund'] = CIKs.loc[CIKs['CIK'].astype(str) == CIK, 'COMPANY_NAME'].iloc[0]
        df['Form'] = filing.split("_")[1]
        date = datetime.strptime(filing.split("_")[2], '%Y-%m-%d')
        df['Quarter_Filed'] = str(date.year) + 'Q' + str((date.month-1)//3 + 1)
        df['File_Name'] = filing
        # Extract the reporting period
        with open (file_path + filing, "r") as myfile:
            s=myfile.read().replace('\n', '')
        start = s.find('PERIOD OF REPORT') + 18
        df['Report_Period'] = s[start:start + 8]
        
        df = df[['Company','Shares','CIK','Form','Fund','Quarter_Filed','File_Name','Report_Period']].copy()
        df.dropna(inplace = True)
        df.drop_duplicates(inplace = True)
        
        if counter == 1:
            df_master = df
        else:
            df_master = pd.concat([df_master,df])
        
    except:
        print("failed attempt")
        pass

df_master.to_csv('df_master_intermediate.csv', index=False)
print("intermediate results written")

# Apply fuzzy match to company names
df_master['Name'] = df_master.apply(lambda row: fuzzy_match(row['Company'], companies), axis = 1)

# Bring in additional company data such as Sector, Industry, and Market Cap
df_master = df_master.merge(companies, on='Name', how='left')


df_master.to_csv('output.csv', index=False)
print("complete")
