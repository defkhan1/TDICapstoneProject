from math import pi
import ast
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pandas as pd
from flask import Flask, render_template, request
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.layouts import row, column
from bokeh.models import ColumnDataSource, CustomJS, Plot, LinearAxis, Grid, Label
from bokeh.models.widgets import Slider, RangeSlider, Button, DataTable, TableColumn, NumberFormatter
from bokeh.models.glyphs import HBar
# from bokeh.core.properties import expr
# from bokeh.models.expressions import CumSum
# from bokeh.transform import cumsum
import numpy as np

app = Flask(__name__)

chains = ['mcdonalds', 'burgerking', 'tacobell', 'wendys', 'chipotle', 'subway', 'starbucks', 'pizzahut', 'dominos', 'dairyqueen', 'kfc', 'sonicdrivein', 'chickfila', 'panerabread', 'dunkindonuts']#, 'mcdoph', 
colors = ['#FFC72C', '#faaf18', '#682A8D', '#ed1b24', '#451400', '#005542', '#036635', '#ee3a43', '#006491', '#EE3E42', '#a3080c', '#EF3B44', '#E51636', '#FFDB87', '#E11383']

chains2 = ['burgerking', 'tacobell', 'wendys', 'chipotle', 'Starbucks', 'PizzaHut', 'Dominos', 'KFC', 'sonicdrivein', 'DunkinDonuts', 'McDonalds']
chains2l = [i.lower() for i in chains2]
colors2 = ['#faaf18', '#682A8D', '#ed1b24', '#451400', '#036635', '#ee3a43', '#006491', '#a3080c', '#EF3B44', '#E11383', '#FFC72C']
names2 = ['Burger King', 'Taco Bell', "Wendy's", 'Chipotle', 'Starbucks', 'Pizza Hut', "Domino's Pizza", 'KFC', 'Sonic Drive-In', "Dunkin' Donuts", "McDonald's"]
colordict = dict(zip(chains2, colors2))
namedict = dict(zip(chains2l, names2))
namedict['sonic'] = 'Sonic Drive-In'
namedictFB = dict(zip(chains2l, chains2))
namedictFB['sonic'] = 'sonicdrivein'

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
	dfTemp = df[['username','talking_about_count','time']].loc[df[['username','talking_about_count','time']]['username'] == namedictFB[name]]
	plot = figure(x_axis_type="datetime", plot_width=775, title="Talking About Count For %s" %namedict[name])
	plot.grid.grid_line_alpha=2.0
	plot.xaxis.axis_label = 'Date'
	plot.yaxis.axis_label = 'Talking About Count'
	plot.line(pd.to_datetime(dfTemp['time']), dfTemp['talking_about_count'], color='#0000FF')#, legend='%s: %s' %(ticker,price))
	#plot.legend.location = "top_left"
	script, div = components(plot)
	return script, div

def makeRanking (df, time):
	clist = list(df['Chain'])
	taclist = list(df['People Talking About This']/1000.0)
	color = list(df['Color'])

	plot = figure(y_range=clist[::-1], plot_height=700, plot_width=550, title="Fast Food Chain Popularity For %s" %time,
	           toolbar_location=None, tools="")

	plot.hbar(y=clist, right=taclist, height=0.5, color=color)

	plot.ygrid.grid_line_color = None
	plot.x_range.start = 0

	plot.xaxis.axis_label = 'People Talking About This (Thousands)'
	plot.xaxis.axis_label_text_font_size = "12pt"
	plot.xaxis.major_label_text_font = "4pt"
	plot.yaxis.major_label_text_font = "4pt"

	return components(plot)

def makeRanking2 (df):
	clist = list(df['name'])
	taclist = list(df['count'])
	color = list(df['color'])

	plot = figure(y_range=clist[::-1], plot_height=400, plot_width=550, title="Weekly Leaders in Popularity",
	           toolbar_location=None, tools="")

	plot.hbar(y=clist, right=taclist, height=0.5, color=color)

	plot.ygrid.grid_line_color = None
	plot.x_range.start = 0

	plot.xaxis.axis_label = 'Number of Weeks as Leader'
	plot.xaxis.axis_label_text_font_size = "12pt"
	plot.xaxis.major_label_text_font = "4pt"
	plot.yaxis.major_label_text_font = "4pt"

	return components(plot)

def processRanking (time, data):
	dataSorted = sorted(data, key = lambda x: x[1][time], reverse = True)
	todaySorted = [(n+1,dataSorted[n][0],dataSorted[n][1][time],dataSorted[n][3]) for n in range(len(chains))]
	dfTodaySorted = pd.DataFrame(data=todaySorted, columns=['Rank','Chain', 'People Talking About This', 'Color'])
	return dfTodaySorted

def processRankingHist (week, data):
	data['time'] = pd.to_datetime(data['time']).apply(lambda data: datetime(year=data.year, month=data.month, day=data.day))
	data.set_index(data['time'],inplace=True)
	Sweek = data.groupby('username')['talking_about_count'].resample('W').mean()
	dfWeek = pd.DataFrame(Sweek)
	dfWeek = dfWeek.reset_index(level=['username', 'time'])
	dfSlice = dfWeek.loc[dfWeek['time'] == week]
	dfSlice.insert(0,'Rank', [i+1 for i in range(len(dfSlice))])
	dfSlice.insert(1,'Chain', [namedict[i.lower()] for i in list(dfSlice['username'])])
	dfSlice.insert(5,'Color', [colordict[i] for i in list(dfSlice['username'])])
	dfSlice = dfSlice.drop(columns=['time','username'])
	dfSlice.rename(columns={'talking_about_count':'People Talking About This'}, inplace=True)
	dfSlice = dfSlice.sort_values(by=['People Talking About This'], ascending=False)
	return dfSlice

def streak(df):
	leadlist = list(df['username'])
	j = 1
	s = leadlist[0]
	jmax = 0
	for i in leadlist[1:]:
		if i == s:
			j += 1
		else:
			if j >= jmax:
				jmax = j
				smax = s
			s = i
			j = 1
	return smax, jmax


@app.route('/', methods=['GET','POST'])
def index():
	time = '2019-04-10'
	dfSB = pd.read_csv('chain_data2modified.csv')
	dfSB.insert(4, 'Color', colors)
	dataExt = [(i[1],ast.literal_eval(i[2]), ast.literal_eval(i[3]), i[4]) for i in dfSB.values]
	timeInd = dataExt[0][2].index(time)
	dfTodaySorted = processRanking (timeInd, dataExt)
	script, div = makeRanking(dfTodaySorted, time)

	# allData = [(getData(chains[i])[0], getData(chains[i])[1], getData(chains[i])[2], colors[i]) for i in range(len(chains))]
	# time = 0
	# dfTodaySorted = processRanking (time, allData)
	# time2 = '2019-04-10'
	# script, div = makeRanking(dfTodaySorted, time2)

	dfHist = pd.read_csv('chain_data_hist.csv')
	dfHist['time'] = pd.to_datetime(dfHist['time']).apply(lambda dfHist: datetime(year=dfHist.year, month=dfHist.month, day=dfHist.day))
	dfHist.set_index(dfHist['time'],inplace=True)
	Sweek = dfHist.groupby('username')['talking_about_count'].resample('W').mean()
	dfWeek = pd.DataFrame(Sweek)
	dfWeek = dfWeek.reset_index(level=['username', 'time'])

	weekList = sorted([str(pd.to_datetime(i).date()) for i in dfWeek['time'].unique() if pd.to_datetime(i).date() > pd.to_datetime('2015-11-29').date()], reverse=True)
	# sorted(list(dfWeek['time'].unique()),reverse=True)

	leaders = dfWeek.loc[pd.to_datetime(dfWeek['time'])>pd.to_datetime('2015-11-29')].sort_values('talking_about_count', ascending=False).drop_duplicates(['time']).sort_values('time')

	leaderCount = leaders.groupby('username')['talking_about_count'].count()

	leaderCount = leaderCount.reset_index(name='count').rename(columns={'index':'username'})
	leaderCount['angle'] = leaderCount['count']/leaderCount['count'].sum() * 2*pi
	leaderCount['color'] = [colordict[i] for i in leaderCount['username']]
	leaderCount['name'] = [namedict[i.lower()] for i in leaderCount['username']]
	leaderCount = leaderCount.sort_values(by=['count'], ascending=False)

	script_pie, div_pie = makeRanking2(leaderCount)

	curleader = list(dfTodaySorted['Chain'])[0]
	allleader = list(leaderCount['name'])[0]

	smax, jmax = streak(leaders)

	maxname, maxtime, maxcount = list(leaders.loc[leaders['talking_about_count'].idxmax()])
	maxtime = str(pd.to_datetime(maxtime).date())
	maxcount = "{:.2e}".format(maxcount)

	# legdict = dict(zip(list(leaderCount.sort_values(by=['count'])['name']),list(leaderCount.sort_values(by=['count'])['count'])))

	# percents = [0]+list(leaderCount['count'].sort_values().cumsum()/leaderCount['count'].sum())
	# starts = [p*2*pi for p in percents[:-1]]
	# ends = [p*2*pi for p in percents[1:]]

	# p = figure(x_range=(-1.05,1.05), y_range=(-1.05,1.05), plot_width=400, plot_height=400, title="Most Popular Chain By Week")

	# p.wedge(x=0, y=0, radius=1, start_angle=starts, end_angle=ends, color=[colordict[i] for i in leaderCount.sort_values(by=['count'])['username']])

	# label1 = Label(x=-0.35, y=-0.5, text='Starbucks: %d' %legdict['Starbucks'], text_color = 'white')
	# label2 = Label(x=-0.85, y=0.3, text='Burger King: %d' %legdict['Burger King'], text_color = 'white')
	# label3 = Label(x=0, y=0.5, text='Sonic', text_color = 'white')
	# label4 = Label(x=0.4, y=0.5, text='T. Bell', text_color = 'white')
	# p.add_layout(label1)
	# p.add_layout(label2)
	# p.add_layout(label3)
	# p.add_layout(label4)

	# p.axis.axis_label=None
	# p.axis.visible=False
	# p.grid.grid_line_color = None

	# script_pie, div_pie = components(p)

	# p = figure(plot_height=350, title="Pie Chart", toolbar_location=None,
	#            tools="hover", x_range=(-0.5, 1.0))
	# tooltips="@name: @count",

	# p.wedge(x=0, y=1, radius=0.4,
	#         start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),
	#         start_angle=expr(CumSum(field='angle', include_zero=True)), end_angle=expr(CumSum(field='angle', include_zero=False )),
	#         line_color="white", fill_color='color', legend='name', source=data)

	return render_template('index.html', div = div, script = script, script_pie = script_pie, div_pie = div_pie, weekList = weekList, curleader = curleader, time = time, allleader = allleader, smax = smax, jmax = jmax, maxname = maxname, maxtime = maxtime, maxcount = maxcount)

@app.route('/graph', methods=['GET','POST'])
def graph():
	# ticker, price, year = request.form['tickerInput'].upper(), request.form['priceInput'], request.form['yearInput']
	
	#Somewhat sloppy way of doing error checking...
	# if ticker == '' or year == '':
	# 	df = None
	# else:
	# 	year = int(year)	
	# 	df = processData(ticker, year, price)
	name = request.form['nameInput'].lower().replace(' ', '').replace("'","").replace('-','')
	dfHist = pd.read_csv('chain_data_hist.csv')

	script, div = makePlot(dfHist, name)
	return render_template('graph.html', div = div, script = script, realname = namedictFB[name], realrealname = namedict[name])

	# if type(df) == pd.DataFrame:
	# 	script, div = makePlot(df, ticker, year, price)
	# 	return render_template('graph.html', div = div, script = script)
		
	# else:
	# 	err = 'Uhoh! Something went wrong. :( Either we do not have data for that ticker/year combo or you entered an invalid ticker and/or year. Please enter a valid ticker and year.'
	# 	return render_template('index.html', err=err)

@app.route('/rank', methods=['GET', 'POST'])
def rank():

	# allData = [(getData(chains[i])[0], getData(chains[i])[1], getData(chains[i])[2], colors[i]) for i in range(len(chains))]
	# time = 0
	# time2 = '2019-04-10'
	# dfTodaySorted = processRanking (time, allData)
	# script, div = makeRanking(dfTodaySorted, time2)

	time = '2019-04-10'
	dfSB = pd.read_csv('chain_data2modified.csv')
	dfSB.insert(4, 'Color', colors)
	dataExt = [(i[1],ast.literal_eval(i[2]), ast.literal_eval(i[3]), i[4]) for i in dfSB.values]
	timeInd = dataExt[0][2].index(time)
	dfTodaySorted = processRanking (timeInd, dataExt)
	script, div = makeRanking(dfTodaySorted, time)

	# week = '2017-07-09'
	week = request.form['weekList']
	dfHist = pd.read_csv('chain_data_hist.csv')
	
	dfSlice = processRankingHist(week, dfHist)

	script_hist, div_hist = makeRanking(dfSlice, week)

	return render_template('rank.html', div = div, script = script, div_hist = div_hist, script_hist = script_hist)

if __name__ == '__main__':
	app.run(port=33507)