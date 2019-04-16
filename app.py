import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pandas as pd
from flask import Flask, render_template, request
from bokeh.plotting import figure
from bokeh.embed import components

app = Flask(__name__)

chains = ['mcdonalds', 'burgerking', 'tacobell', 'wendys', 'chipotle', 'subway', 'starbucks', 'pizzahut', 'dominos', 'dairyqueen', 'kfc', 'sonicdrivein', 'chickfila', 'panerabread', 'dunkindonuts', 'mcdoph']

def getSoup(chain):
    r = requests.get("https://socialblade.com/facebook/page/"+chain).text
    soup = BeautifulSoup(r, 'html.parser')
    return soup

def getData(chain):
    soup = getSoup(chain)
    souptext = soup.text
    chartIndex = souptext.index("Highcharts.chart('graph-facebook-daily-vidviews-container'")
    chart = souptext[chartIndex:chartIndex+1000]
    name = chart[chart.find("\\'")+2:chart.find("\\''")] 
    tac = chart[chart.find('data: [')+7:chart.find('] }]')] 
    tac = list(map(int, tac.split(',')))
    datestart = souptext[souptext.find("( ")+2:souptext.find("( ")+12]
    datestart2 = datetime.strptime(datestart,'%Y-%m-%d')
    dates = [datestart2 + i*timedelta(days=1) for i in range(14)]
    datesstr = [datetime.strftime(i, '%Y-%m-%d') for i in dates]
    return name, tac, datesstr

def makePlot (df, name):
	dfTemp = df[['username','talking_about_count','time']].loc[df[['username','talking_about_count','time']]['username'] == name]
	plot = figure(x_axis_type="datetime", title="Talking About Count For %s" %name)
	plot.grid.grid_line_alpha=2.0
	plot.xaxis.axis_label = 'Date'
	plot.yaxis.axis_label = 'Talking About Count'
	plot.line(pd.to_datetime(dfTemp['time']), dfTemp['talking_about_count'], color='#0000FF')#, legend='%s: %s' %(ticker,price))
	#plot.legend.location = "top_left"
	script, div = components(plot)
	return script, div

@app.route('/', methods=['GET','POST'])
def index():
	day = 0
	allData = [getData(chain) for chain in chains]
	dataSorted = sorted(allData, key = lambda x: x[1][day], reverse = True)
	df = pd.DataFrame(data=allData, columns=['Name', 'Talking About', 'Dates'])
	dfSorted = pd.DataFrame(data=dataSorted, columns=['Name', 'Talking About', 'Dates'])
	todaySorted = [(n+1,dataSorted[n][0],dataSorted[n][1][day]) for n in range(14)]
	dfTodaySorted = pd.DataFrame(data=todaySorted, columns=['Rank','Chain', 'People Talking About This'])
	dfTodaySorted.set_index('Rank')


	# return render_template('index.html', chain = chain, tac = tac)
	return render_template('index.html', tables=[dfTodaySorted.to_html(classes='data', index = False)])

@app.route('/graph', methods=['GET','POST'])
def graph():
	# ticker, price, year = request.form['tickerInput'].upper(), request.form['priceInput'], request.form['yearInput']
	
	#Somewhat sloppy way of doing error checking...
	# if ticker == '' or year == '':
	# 	df = None
	# else:
	# 	year = int(year)	
	# 	df = processData(ticker, year, price)
	name = request.form['nameInput']
	dfHist = pd.read_csv('chain_data_hist.csv')

	script, div = makePlot(dfHist, name)
	return render_template('graph.html', div = div, script = script)

	# if type(df) == pd.DataFrame:
	# 	script, div = makePlot(df, ticker, year, price)
	# 	return render_template('graph.html', div = div, script = script)
		
	# else:
	# 	err = 'Uhoh! Something went wrong. :( Either we do not have data for that ticker/year combo or you entered an invalid ticker and/or year. Please enter a valid ticker and year.'
	# 	return render_template('index.html', err=err)

if __name__ == '__main__':
	app.run(port=33507)