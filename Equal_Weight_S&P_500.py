import numpy as np
import pandas as pd
import requests
import xlsxwriter
import math
#from secrets import IEX_CLOUD_API_TOKEN


stocks = pd.read_csv("sp_500_stocks.csv")
#print(stocks)

symbol = 'AAPL'
#token = IEX_CLOUD_API_TOKEN
token = 'Tpk_059b97af715d417d9f49f50b51b1c448'
api_url = f'https://sandbox.iexapis.com/stable/stock/{symbol}/quote/?token={token}'
data = requests.get(api_url)
#check that request is status 200
#print(data.status_code == 200)
data = requests.get(api_url).json()
#print(data)

price = data['latestPrice']
market_cap = data['marketCap']

my_columns = ['Ticker', 'Stock Price', 'Market Capitalization', 'Number of Shares to Buy']
final_dataframe = pd.DataFrame(columns = my_columns)
final_dataframe = final_dataframe.append(
    pd.Series(
    [
     symbol,
     price,
     market_cap,
     'N/A'
     ],
    index = my_columns
    ),
    ignore_index=True
)

def chunks(lst,n):
    for i in range(0,len(lst), n):
        yield lst[i:i + n]

symbol_groups = list(chunks(stocks['Ticker'], 100))

symbol_strings = []
for i in range(0, len(symbol_groups)):
    symbol_strings.append(','.join(symbol_groups[i]))
    #print(symbol_strings[i])
    
final_dataframe = pd.DataFrame(columns=my_columns)

for symbol_string in symbol_strings:
    batch_api_call_url = f'https://sandbox.iexapis.com/stable/stock/market/batch?symbols={symbol_string}&types=quote&token={token}'
    #print(batch_api_call_url)
    #data = requests.get(batch_api_call_url)
    #print(data.status_code == 200)
    data = requests.get(batch_api_call_url).json()
    for symbol in symbol_string.split(','):
        final_dataframe = final_dataframe.append(
        pd.Series(
        [
         symbol,
         data[symbol]['quote']['latestPrice'],
         data[symbol]['quote']['marketCap'],
         'N/A'
         ],
        index = my_columns
        ),
        ignore_index=True
    )

#print(final_dataframe)

portfolio_size = input('Enter the value of your portfolio: ')

try:
    val = float(portfolio_size)
except ValueError:
    print("That is not a number! \nPlease try again:")
    portfolio_size = input('Enter the value of your portfolio: ')
    val = float(portfolio_size)
    
position_size = val/len(final_dataframe.index)
#number_of_apple_shares = position_size/500
#print(math.floor(number_of_apple_shares))

for i in range(0, len(final_dataframe.index)):
    final_dataframe.loc[i, 'Number of Shares to Buy'] = math.floor(position_size/final_dataframe.loc[i, 'Stock Price'])

writer = pd.ExcelWriter('recommended trades.xlsx', engine = 'xlsxwriter')
        
final_dataframe.to_excel(writer, 'Recommended Trades', index = False)


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


column_formats = {
    'A': ['Ticker', string_format],
    'B': ['Stock Price', dollar_format],
    'C': ['Market Capitalization', dollar_format],
    'D': ['Number of Shares to Buy', integer_format],
    }



for column in column_formats.keys():
    writer.sheets['Recommended Trades'].set_column(f'{column}:{column}', 18, column_formats[column][1])
    writer.sheets['Recommended Trades']. write(f'{column}1',column_formats[column][0], column_formats[column][1])
    
writer.save()
writer.close()


