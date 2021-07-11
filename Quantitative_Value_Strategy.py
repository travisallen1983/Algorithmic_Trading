import numpy as np
import pandas as pd
import requests
import xlsxwriter
from scipy import stats
import math
from statistics import mean

stocks = pd.read_csv('sp_500_stocks.csv')
token = 'Tpk_059b97af715d417d9f49f50b51b1c448'

symbol = 'CNC'
api_url = f'https://sandbox.iexapis.com/stable/stock/{symbol}/quote/?token={token}'
data = requests.get(api_url).json()
#print(data)

price = data['latestPrice']
pe_ratio = data['peRatio']

#print(f'Price = {price} and Pe Ratio = {pe_ratio}')

def chunks(lst,n):
    for i in range(0,len(lst), n):
        yield lst[i:i + n]

symbol_groups = list(chunks(stocks['Ticker'], 100))

symbol_strings = []
for i in range(0, len(symbol_groups)):
    symbol_strings.append(','.join(symbol_groups[i]))
    #print(symbol_strings[i])
    
my_columns = ['Ticker', 'Price', 'Price-to-Earnings Ratio', 'Number of Shares to Buy']

final_dataframe = pd.DataFrame(columns = my_columns)
for symbol_string in symbol_strings:
    batch_api_call_url =  f'https://sandbox.iexapis.com/stable/stock/market/batch?symbols={symbol_string}&types=quote&token={token}'
    data = requests.get(batch_api_call_url).json()
    for symbol in symbol_string.split(','):
        final_dataframe = final_dataframe.append(
            pd.Series(
                [
                    symbol,
                    data[symbol]['quote']['latestPrice'],
                    data[symbol]['quote']['peRatio'],
                    'N/A'
                    
                ],
                index = my_columns
               ), ignore_index = True
            )
        
#print(final_dataframe)

final_dataframe.sort_values('Price-to-Earnings Ratio', ascending = True, inplace=True)
final_dataframe = final_dataframe[final_dataframe['Price-to-Earnings Ratio'] > 0]
final_dataframe = final_dataframe[:50]
final_dataframe.reset_index(inplace = True)
final_dataframe.drop('index', axis=1, inplace = True)

def portfolio_input():
    global portfolio_size
    portfolio_size = input('Enter the value of your portfolio: ')

    try:
        float(portfolio_size)
    except ValueError:
        print("That is not a number! \nPlease try again:")
        portfolio_size = input('Enter the value of your portfolio: ')
        float(portfolio_size)

portfolio_input()
position_size = float(portfolio_size)/len(final_dataframe.index)

for row in final_dataframe.index:
    final_dataframe.loc[row, 'Number of Shares to Buy'] = math.floor(position_size/final_dataframe.loc[row, 'Price'])


symbol = 'CNC'
batch_api_call_url =  f'https://sandbox.iexapis.com/stable/stock/market/batch?symbols={symbol}&types=quote,advanced-stats&token={token}'
data = requests.get(batch_api_call_url).json()
pe_ratio = data[symbol]['quote']['peRatio']
pb_ratio = data[symbol]['advanced-stats']['priceToBook']
ps_ratio = data[symbol]['advanced-stats']['priceToSales']
enterprise_value = data[symbol]['advanced-stats']['enterpriseValue']
ebitda = data[symbol]['advanced-stats']['EBITDA']
gross_profit = data[symbol]['advanced-stats']['grossProfit']
ev_to_ebitda = enterprise_value/ebitda
ev_to_gross_profit = enterprise_value/gross_profit

rv_columns = [
    'Ticker',
    'Price',
    'Number of Shares to Buy',
    'Price-to-Earnings Ratio',
    'PE Percentile',
    'Price-to-Book Ratio',
    'PB Percentile',
    'Price-to_Sales Ratio',
    'PS Percentile',
    'EV/EBITDA',
    'EV/EBITDA Percentile',
    'EV/GP',
    'EV/GP Percentile',
    'RV Score'
    ]
rv_dataframe = pd.DataFrame(columns = rv_columns)

for symbol_string in symbol_strings:
    batch_api_call_url =  f'https://sandbox.iexapis.com/stable/stock/market/batch?symbols={symbol_string}&types=quote,advanced-stats&token={token}'
    data = requests.get(batch_api_call_url).json()
    for symbol in symbol_string.split(','):
        enterprise_value = data[symbol]['advanced-stats']['enterpriseValue']
        ebitda = data[symbol]['advanced-stats']['EBITDA']
        gross_profit = data[symbol]['advanced-stats']['grossProfit']
        try:
            ev_to_ebitda = enterprise_value/ebitda
        except TypeError:
            ev_to_ebitda = np.NaN
        try:
            ev_to_gross_profit = enterprise_value/gross_profit
        except TypeError:
            ev_to_gross_profit = np.NaN
        
        rv_dataframe = rv_dataframe.append(
            pd.Series(
                [
                    symbol,
                    data[symbol]['quote']['latestPrice'],
                    'N/A',
                    data[symbol]['quote']['peRatio'],
                    'N/A',
                    data[symbol]['advanced-stats']['priceToBook'],
                    'N/A',
                    data[symbol]['advanced-stats']['priceToSales'],
                    'N/A',
                    ev_to_ebitda,
                    'N/A',
                    ev_to_gross_profit,
                    'N/A',
                    'N/A'
                ], index = rv_columns
                ),ignore_index = True
            )
        
#print(rv_dataframe[rv_dataframe.isnull().any(axis=1)])

for column in ['Price-to-Earnings Ratio','Price-to-Book Ratio',
    'Price-to_Sales Ratio', 'EV/EBITDA','EV/GP']:
    rv_dataframe[column].fillna(rv_dataframe[column].mean(), inplace=True)     


#print(rv_dataframe[rv_dataframe.isnull().any(axis=1)]) 

metrics = {
    'Price-to-Earnings Ratio': 'PE Percentile',
    'Price-to-Book Ratio': 'PB Percentile',
    'Price-to_Sales Ratio': 'PS Percentile',
    'EV/EBITDA': 'EV/EBITDA Percentile',
    'EV/GP': 'EV/GP Percentile'
    }

for metric in metrics.keys():
    for row in rv_dataframe.index:
        rv_dataframe.loc[row, metrics[metric]] = stats.percentileofscore(rv_dataframe[metric], rv_dataframe.loc[row, metric])/100

for row in rv_dataframe.index:
    value_percentiles = []
    for metric in metrics.keys():
        value_percentiles.append(rv_dataframe.loc[row, metrics[metric]]) 
    rv_dataframe.loc[row, 'RV Score'] = mean(value_percentiles)
rv_dataframe.sort_values('RV Score', ascending = True, inplace = True)
rv_dataframe = rv_dataframe[:50]
rv_dataframe.reset_index(drop = True, inplace=True)

#portfolio_input()
position_size = float(portfolio_size)/len(rv_dataframe.index)

for row in final_dataframe.index:
    rv_dataframe.loc[row, 'Number of Shares to Buy'] = math.floor(position_size/rv_dataframe.loc[row, 'Price'])

writer = pd.ExcelWriter('value_strategy.xlsx', engine = 'xlsxwriter')
        
rv_dataframe.to_excel(writer, sheet_name = 'Value Strategy', index = False)


background_color = '#0a0a23'
font_color = '#ffffff'

string_format = writer.book.add_format(
    {
     'font_color': font_color,
     'bg_color': background_color,
     'border': 1
     }
    )
dollar_format = writer.book.add_format(
    {
     'num_format': '$0.00',
     'font_color': font_color,
     'bg_color': background_color,
     'border': 1
     }
    )
integer_format = writer.book.add_format(
    {
     'num_format': '0',
     'font_color': font_color,
     'bg_color': background_color,
     'border': 1
     }
    )

float_format = writer.book.add_format(
    {
     'num_format': '0.00',
     'font_color': font_color,
     'bg_color': background_color,
     'border': 1
     }
    )

percent_format = writer.book.add_format(
    {
     'num_format': '0.0%',
     'font_color': font_color,
     'bg_color': background_color,
     'border': 1
     }
    )


column_formats = {
    'A': ['Ticker', string_format],
    'B': ['Price', dollar_format],
    'C': ['Number of Shares to Buy', integer_format],
    'D': ['Price-to-Earnings Ratio', float_format],
    'E': ['PE Percentile', percent_format],
    'F': ['Price-to-Book Ratio', float_format],
    'G': ['PB Percentile', percent_format],
    'H': ['Price-to_Sales Ratio', float_format],
    'I': ['PS Percentile', percent_format],
    'J': ['EV/EBITDA', float_format],
    'K': ['EV/EBITDA Percentile', percent_format],
    'L': ['EV/GP', float_format],
    'M': ['EV/GP Percentile', percent_format],
    'N': ['RV Score', percent_format]
   
    }



for column in column_formats.keys():
    writer.sheets['Value Strategy'].set_column(f'{column}:{column}', 25, column_formats[column][1])
    writer.sheets['Value Strategy']. write(f'{column}1',column_formats[column][0], column_formats[column][1])
    
writer.save()
writer.close()