import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

data = pd.read_csv('daily_files.csv', header=None, index_col=0, parse_dates=True)
data.rename({0: 'Dzien pomiaru', 1: 'Ilosc plikow avi', 2: 'Ilosc plikow csv'})
# print(data.head())
# fig, ax = plt.subplots()

# ax = data.plot(style=['o', 'x'], ms=6, grid=True, legend=True,
#                title='Ilosc plikow generowanych dziennie 11.11.2017 - 10.12.2017')
# ax = (data[1] - data[2]).abs().plot()
# plt.scatter(data[0], data[1])
# plt.scatter(data[0], data[2])
# ax.set_xlabel('Dzien pomiaru')
# ax.set_ylabel('Ilosc plikow')
# ax.xaxis.set_major_locator(mdates.DayLocator())
# ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y:%m:%D'))
# plt.show()

summary_amount_of_files = data.sum()[1]
print(data[1].describe())
seconds_in_days_counted = (data.shape[0] * 24 * 60 * 60)
amount_of_seconds_between_files = seconds_in_days_counted / summary_amount_of_files
print("Amount of file pairs: {}".format(summary_amount_of_files))
print("Amount of days: {}".format(data.shape[0]))
print("Amount of seconds: {}".format(seconds_in_days_counted))
print("Mean time between files {:.2f} s".format(amount_of_seconds_between_files))