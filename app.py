import os
import csv
import talib
import ccxt
import pandas
from flask import Flask, escape, request, render_template
from patterns import candlestick_patterns

app = Flask(__name__)


exchange = ccxt.binance()
exchange.loadMarkets()

tf = '1d'

@app.route('/loadusdtpairsonbinance')
def loadusdtpairsonbinance():
    symbols = exchange.symbols
    suffix = '/USDT'
    symbols = filter(lambda x: x.endswith(suffix), symbols)
    return render_template('symbols.html', symbols=symbols)

@app.route('/snapshot')
def snapshot():
    with open('cryptodatasets/symbols.csv') as f:
        for line in f:
            eachline = line.strip().split(',')[0]
            symbol = eachline
            fileSymbol = symbol.replace('/', '_')
            data = exchange.fetch_ohlcv(symbol, timeframe=tf, limit=100)
            df = pandas.DataFrame(data, columns=['time', 'Open', 'High', 'Low', 'Close', 'Volume'])
            print(data)
            df.to_csv('cryptodatasets/daily/{}.csv'.format(fileSymbol))

    return {
        "code": "success"
    }


@app.route('/')
def index():
    pattern = request.args.get('pattern', False)
    stocks = {}

    with open('cryptodatasets/symbols.csv') as f:
        for row in csv.reader(f):
            stocks[row[0].replace('/','_')] = {'company': row[0].replace('/','')}

    if pattern:
        for filename in os.listdir('cryptodatasets/daily'):
            df = pandas.read_csv('cryptodatasets/daily/{}'.format(filename))
            pattern_function = getattr(talib, pattern)
            symbol = filename.split('.')[0]

            try:
                results = pattern_function(
                    df['Open'], df['High'], df['Low'], df['Close'])
                last = results.tail(1).values[0]
                if last > 0:
                    stocks[symbol][pattern] = 'bullish'
                elif last < 0:
                    stocks[symbol][pattern] = 'bearish'
                else:
                    stocks[symbol][pattern] = None
            except Exception as e:
                print(e)
                print('failed on filename: ', filename)
    
    print(stocks)
    return render_template('index.html', candlestick_patterns=candlestick_patterns, stocks=stocks, pattern=pattern)
