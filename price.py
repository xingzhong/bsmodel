import mibian
from pandas.io.data import Options
from datetime import date, timedelta
from pandas.tseries.offsets import BDay
from flask import Flask
app = Flask(__name__)

RiskFREE = 0.01

def processCall(data):
	bs = mibian.BS(
		[data.Underlying_Price, data.strikePrice, RiskFREE, data.d2e ],
		callPrice=(data.Bid+data.Ask)/2)
	iv = bs.impliedVolatility
	bsIV = mibian.BS(
		[data.Underlying_Price, data.strikePrice, RiskFREE, data.d2e ],
		volatility=iv)
	data['adjIV'] = iv
	data['est'] = bsIV.callPrice
	data['delta'] = bsIV.callDelta
	data['theta'] = bsIV.callTheta
	data['rho'] = bsIV.callRho
	data['vega'] = bsIV.vega
	data['gamma'] = bsIV.gamma
	#import ipdb; ipdb.set_trace()
	return data

def processPut(data):
	bs = mibian.BS(
		[data.Underlying_Price, data.strikePrice, RiskFREE, data.d2e ],
		putPrice=(data.Bid+data.Ask)/2)
	iv = bs.impliedVolatility
	bsIV = mibian.BS(
		[data.Underlying_Price, data.strikePrice, RiskFREE, data.d2e ],
		volatility=iv)
	data['adjIV'] = iv
	data['est'] = bsIV.putPrice
	data['delta'] = bsIV.putDelta
	data['theta'] = bsIV.putTheta
	data['rho'] = bsIV.putRho
	data['vega'] = bsIV.vega
	data['gamma'] = bsIV.gamma
	#import ipdb; ipdb.set_trace()
	return data


def fetch(ticker):
	token = Options(ticker, 'yahoo')
	expires = token.expiry_dates
	today = date.today()
	expiry = filter( lambda x: x - today > timedelta(days=25),  expires)[0]
	dayToExpiry = (expiry - today).days
	callChain = token.get_call_data(expiry = expiry).reset_index(level=[1,3], drop=True)
	callChain['strikePrice'] = callChain.index.levels[0]
	callChain['d2e'] = dayToExpiry
	putChain = token.get_put_data(expiry = expiry).reset_index(level=[1,3], drop=True)
	putChain['strikePrice'] = putChain.index.levels[0]
	putChain['d2e'] = dayToExpiry
	callChain = callChain.apply(processCall, axis=1, raw=True)
	putChain = putChain.apply(processPut, axis=1, raw=True)
	#import ipdb; ipdb.set_trace()

	price = token.underlying_price
	chain = callChain.append(putChain)
	chain.drop(["IsNonstandard", 'Underlying', 'Quote_Time',
		 	'Root', 'strikePrice', 'Chg', 'PctChg', 'Underlying_Price'],
		 	axis=1, inplace=True)
	#chain.set_index('', )
	return chain, price, expiry

@app.route("/o/<ticker>")
def chain(ticker):
	chain, price, expiry = fetch(ticker)
	return chain.to_html()

if __name__ == '__main__':
	app.run(port=5001)