import pathlib as pl
import csv
import datetime as dt
import statistics
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import itertools

str_loc = 'lvm_results.csv'
path = pl.Path(str_loc)

data = []
with path.open('r') as fd:
    reader = csv.reader(fd)
    for timestr, sizestr in reader:
        timestamp = dt.datetime.strptime(timestr, '%Y-%m-%d %H:%M:%S').replace(year=2018, month=1, day=1,
                                                                               second=0, microsecond=0)
        # timestamp = dt.datetime.strptime(timestr, '%Y-%m-%d %H:%M:%S').replace(year=2018, month=1, day=1)
        size = int(sizestr)
        # if size:
        #     data.append((timestamp, size))
        data.append((timestamp, size))

data = sorted(data, key=lambda x: x[0])
timestamps = []
mins = []
maxes = []
avgs = []
medians = []

for key, values in itertools.groupby(data, key=lambda x: x[0]):
    values = [val for _, val in values]
    timestamps.append(key)
    mins.append(min(values))
    maxes.append(max(values))
    avgs.append(sum(values)/len(values))
    medians.append(statistics.median(values))

plot_metrics = (
    (mins, 'Minimum'),
    (maxes, 'Maksimum'),
    (avgs, 'Srednia'),
    (medians, 'Mediana')
)

fig, ax = plt.subplots()

for metric, label in plot_metrics:
    ax.plot(timestamps, metric, label=label)
ax.legend()
ax.set_title('Wielkosci plikow lvm w ujeciu dobowym')
# plt.gcf().autofmt_xdate()
ax.xaxis.set_major_locator(mdates.HourLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
ax.set_ylim(bottom=0)
ax.grid()
ax.set_xlabel('Czas pomiaru')
ax.set_ylabel('Wielkosc pliku [Bajty]')

plt.show()
