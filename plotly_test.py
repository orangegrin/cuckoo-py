from plotly.offline import plot
from plotly.graph_objs import Scatter, Box

plot([Scatter(x=[1, 2, 3], y=[3, 1, 6])], filename='./plot-11.html')