import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

data = pd.read_csv('avi_results.csv', header=None, index_col=0, parse_dates=True)
data.rename({0: 'Data pomiaru', 1: 'Wielkosc pliku w bajtach'})

fig, ax = plt.subplots()

data.plot(ax=ax, style='o', ms=3, grid=True, legend=False,
          title='Zaleznosc wielkosci pliku od momentu pomiaru')
ax.set_xlabel('Czas zarejestrowania sekwencji wideo')
ax.set_ylabel('Wielkosc sekwencji wideo [bajty]')
ax.xaxis.set_major_locator(mdates.HourLocator(byhour=[0,1]))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
plt.show()
