
from pandas import datetime
import pandas as pd
from matplotlib import pyplot
 
def parser(x):
	return datetime.strptime('190'+x, '%Y-%m')
 
series = pd.Series()
series.plot()
pyplot.show()
