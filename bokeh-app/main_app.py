import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from bokeh.plotting import figure, save
from bokeh.io import curdoc, show
from bokeh.layouts import row, column, widgetbox, gridplot
from bokeh.models import ColumnDataSource, Legend, DatetimeTickFormatter, Dropdown
from bokeh.models.widgets import Slider, TextInput, Select
from bokeh.io import output_notebook, output_file

from bokeh.application import Application
from bokeh.application.handlers import FunctionHandler


covdat = pd.read_csv("https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Confirmed.csv")
covdat = pd.melt(covdat, id_vars=["Country/Region", "Province/State", "Lat", "Long"], var_name="Dates")
covdat["Dates"] = pd.to_datetime(covdat["Dates"], format = "%m/%d/%y")
covdat["Number_days"] = covdat["Dates"] - covdat["Dates"].min()
covdat["Number_days"] = covdat["Number_days"].astype("timedelta64[D]")
##covdat.head()

covdat_c = covdat.groupby(["Country/Region", "Dates", "Number_days"], as_index=False)[["value"]].sum()
target_countries = ["Australia", "China", "Venezuela", "Japan", "Canada", "Singapore", "United Kingdom", "New Zealand"]
covdat_c = covdat_c[covdat_c["Country/Region"].isin(target_countries)]

country_list = [(country, country) for country in covdat_c["Country/Region"].unique()]


N0 = 1
r = 0.1
dt = 1
Nt = 54
max_Nt = 120
r0 = 1.1

# Numpy linspace takes arguments: start, stop, num
t = np.linspace(0, (max_Nt + 1)* dt, max_Nt + 2)
N = np.zeros(max_Nt + 2)
N_r0 = np.zeros(max_Nt + 2)

N[0] = N0
N_r0[0] = N0

for n in range (max_Nt + 1):
    N[n + 1] = N[n] + r*dt*N[n]
    N_r0[n + 1] = N_r0[n] * r0
    
y1 = N0 * np.exp(r*t)
y2 = N
y3 = N_r0

source = ColumnDataSource(data=dict(x=t, y1=y1, y2=y2, y3=y3))
source_covdat_c = ColumnDataSource(data=dict(x = covdat_c["Number_days"].loc[covdat_c["Country/Region"] == "Australia"],
                                             y = covdat_c["value"].loc[covdat_c["Country/Region"] == "Australia"], 
                                             dates = covdat_c["Dates"].loc[covdat_c["Country/Region"] == "Australia"]))

p1 = figure(plot_height = 400, plot_width = 600, title = "Exponential Growth",
              tools = "crosshair,pan,reset,save,wheel_zoom,hover",
              y_range = [0, 800])

p1.xaxis.axis_label = "Time (days)"
p1.yaxis.axis_label = "Number infected people"

res01 = p1.line('x', 'y1', source=source, line_width=3, line_alpha=0.6, color='blue')
res02 = p1.line('x', 'y2', source=source, line_width=3, line_alpha=0.6, color='red')
res03 = p1.line('x', 'y3', source=source, line_width=3, line_alpha=0.6, color='orange')
res04 = p1.line('x', 'y', source=source_covdat_c, line_width=3, line_alpha=0.6, color='black')

p2 = figure(plot_height = 400, plot_width = 600, title = "Exponential Growth Log Scale",
              tools = "crosshair,pan,reset,save,wheel_zoom,hover", y_axis_type = "log")

p2.xaxis.axis_label = "Time (days)"
p2.yaxis.axis_label = "Number infected people (log scale)"

res01ex = p2.line('x', 'y1', source=source, line_width=3, line_alpha=0.6, color='blue')
res02ex = p2.line('x', 'y2', source=source, line_width=3, line_alpha=0.6, color='red')
res03ex = p2.line('x', 'y3', source=source, line_width=3, line_alpha=0.6, color='orange')
res04ex = p2.line('x', 'y', source=source_covdat_c, line_width=3, line_alpha=0.6, color='black')

legend1 = Legend(items = [("Exp Growth Exact approach", [res01]), ("Exp Growth Numerical approach", [res02]), 
                          ("Exponential Growth r0", [res03]), ("Covid19 cases Australia", [res04])],
                        location = (10,200))
legend2 = Legend(items = [("Exp Growth Exact approach", [res01ex]), ("Exp Growth Numerical approach", [res02ex]), 
                          ("Exponential Growth r0", [res03ex]), ("Covid19 cases Australia", [res04ex])],
                                                                     location = (10,200))

p1.add_layout(legend1)
p2.add_layout(legend2)

# Set up widgets
N0_slider = Slider(title="Initial cases", value=N0, start=1, end=1000, step=1)
r_slider = Slider(title="Discrete Growth Rate", value=r, start=0, end=3, step=0.02)
r0_slider = Slider(title="Basic reproduction number", value=r0, start=0, end=3, step = 0.02)
Nt_slider = Slider(title="Total time (days)", value=Nt, start=10, end=max_Nt, step=1)
country_opts = country_list
dropdown = Select(title="Select Country", value="Australia", options=country_opts)
    
def update_data(attrname, old, new):
    # Get the current slider values
    a = N0_slider.value
    b = r_slider.value
    c = dt
    d = Nt_slider.value
    e = r0_slider.value
    f = dropdown.value
    
    D = np.zeros(d + 2)
    D[0] = a
    
    D_r0 = np.zeros(d + 2)
    D_r0[0] = a
    
    for n in range (d + 1):  
        D[n + 1] = D[n] + b*c*D[n]
        D_r0[n + 1] = D_r0[n] * e
        
    # Generate the new curve
    t1 = np.linspace(0, (d + 1)* dt, d + 2)
    y1 = a * np.exp(b*t1)
    y2 = D
    y3 = D_r0

    source.data = dict(x=t1, y1=y1, y2=y2, y3=y3)
    source_covdat_c.data = dict(x = covdat_c["Number_days"].loc[covdat_c["Country/Region"] == f],
                           y = covdat_c["value"].loc[covdat_c["Country/Region"] == f], 
                           dates = covdat_c["Dates"].loc[covdat_c["Country/Region"] == f])
    
    
for w in [N0_slider, r_slider, r0_slider, Nt_slider, dropdown]:
    w.on_change('value', update_data)

inputs = column(N0_slider, r_slider, r0_slider, Nt_slider, dropdown)
dropdown_col = column(dropdown)
layout = row(column(p1, p2), column(N0_slider, r_slider, r0_slider, Nt_slider), dropdown_col)


curdoc().add_root(layout)
