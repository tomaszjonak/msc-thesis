import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

data = pd.read_csv('daily_files.csv', header=None, index_col=0, parse_dates=True)
data.rename({0: 'Dzien pomiaru', 1: 'Ilosc plikow avi', 2: 'Ilosc plikow csv'})

# fig, ax = plt.subplots()

# ax = data.plot(style=['o', 'x'], ms=6, grid=True, legend=True,
#                title='Ilosc plikow generowanych dziennie 11.11.2017 - 10.12.2017')
ax = (data[1] - data[2]).abs().plot()
# plt.scatter(data[0], data[1])
# plt.scatter(data[0], data[2])
ax.set_xlabel('Dzien pomiaru')
ax.set_ylabel('Ilosc plikow')
ax.xaxis.set_major_locator(mdates.DayLocator())
# ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y:%m:%D'))
plt.show()
