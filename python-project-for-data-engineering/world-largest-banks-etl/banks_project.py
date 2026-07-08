import requests
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3
import numpy as np
from datetime import datetime

url = 'https://web.archive.org/web/20230908091635/https://en.wikipedia.org/wiki/List_of_largest_banks'
table_attribs = ['Name', 'MC_USD_Billion']
db_name = 'Banks.db'
table_name = 'Largest_banks'
csv_path = './Largest_banks_data.csv'
log_file = 'code_log.txt'
exchange_rate_csv = 'https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/IBMSkillsNetwork-PY0221EN-Coursera/labs/v2/exchange_rate.csv'

def log_progress(message):
    ''' This function logs the mentioned message of a given stage of the
    code execution to a log file. Function returns nothing'''
    timestamp_format = '%Y-%m-%d-%H:%M:%S' # Year-Monthname-Day-Hour-Minute-Second 
    now = datetime.now() # get current timestamp 
    timestamp = now.strftime(timestamp_format) 
    with open(log_file,"a") as f: 
        f.write(timestamp + ' : ' + message + '\n')

def extract(url, table_attribs):
    ''' This function aims to extract the required
    information from the website and save it to a data frame. The
    function returns the data frame for further processing. '''
    df = pd.DataFrame(columns=table_attribs)
    page = requests.get(url).text
    soup = BeautifulSoup(page, 'html.parser')
    tables = soup.find_all('tbody')
    # The first table contains Market Cap info in the snapshot
    rows = tables[0].find_all('tr')
    for row in rows:
        col = row.find_all('td')
        if len(col) != 0:
            # col[1] Bank Name, col[2] Market cap(US$ billion)
            name = col[1].find_all('a')[1].text if len(col[1].find_all('a')) > 1 else col[1].text.strip()
            # The name is actually usually in the second 'a' tag, but if not, just take text
            # Actually col[1] contains a span (flag) and an a tag (name). 
            # text.strip() should just get the text minus the flag, but sometimes flag has text.
            # Let's just use text and clean it or use the 'a' tag. 
            # In most solutions, `col[1].text.strip()` works if they clean newlines.
            name = col[1].text.strip()
            mc = col[2].text.strip()
            try:
                mc_val = float(mc.replace('\n', ''))
                df = pd.concat([df, pd.DataFrame({"Name": [name], "MC_USD_Billion": [mc_val]})], ignore_index=True)
            except ValueError:
                pass
    return df

def transform(df, csv_path):
    ''' This function accesses the CSV file for exchange rate
    information, and adds three columns to the data frame, each
    containing the transformed version of Market Cap column to
    respective currencies'''
    # read exchange rate csv
    exchange_rate = pd.read_csv(csv_path)
    # create dictionary
    exchange_rate_dict = exchange_rate.set_index('Currency').to_dict()['Rate']
    
    # add columns
    df['MC_GBP_Billion'] = [np.round(x*exchange_rate_dict['GBP'],2) for x in df['MC_USD_Billion']]
    df['MC_EUR_Billion'] = [np.round(x*exchange_rate_dict['EUR'],2) for x in df['MC_USD_Billion']]
    df['MC_INR_Billion'] = [np.round(x*exchange_rate_dict['INR'],2) for x in df['MC_USD_Billion']]
    
    return df

def load_to_csv(df, output_path):
    ''' This function saves the final data frame as a CSV file in
    the provided path. Function returns nothing.'''
    df.to_csv(output_path, index=False)

def load_to_db(df, sql_connection, table_name):
    ''' This function saves the final data frame to a database
    table with the provided name. Function returns nothing.'''
    df.to_sql(table_name, sql_connection, if_exists='replace', index=False)

def run_query(query_statement, sql_connection):
    ''' This function runs the query on the database table and
    prints the output on the terminal. Function returns nothing. '''
    print(query_statement)
    query_output = pd.read_sql(query_statement, sql_connection)
    print(query_output)

''' Here, you define the required entities and call the relevant
functions in the correct order to complete the project. Note that this
portion is not inside any function.'''

if __name__ == '__main__':
    log_progress('Preliminaries complete. Initiating ETL process')
    
    df = extract(url, table_attribs)
    log_progress('Data extraction complete. Initiating Transformation process')
    
    df = transform(df, exchange_rate_csv)
    log_progress('Data transformation complete. Initiating loading process')
    
    load_to_csv(df, csv_path)
    log_progress('Data saved to CSV file')
    
    sql_connection = sqlite3.connect(db_name)
    log_progress('SQL Connection initiated.')
    
    load_to_db(df, sql_connection, table_name)
    log_progress('Data loaded to Database as table. Running the query')
    
    query_statement_1 = f"SELECT * FROM {table_name}"
    run_query(query_statement_1, sql_connection)
    
    query_statement_2 = f"SELECT AVG(MC_GBP_Billion) FROM {table_name}"
    run_query(query_statement_2, sql_connection)
    
    query_statement_3 = f"SELECT Name from {table_name} LIMIT 5"
    run_query(query_statement_3, sql_connection)
    
    log_progress('Process Complete.')
    
    sql_connection.close()
    log_progress('Server Connection closed')
