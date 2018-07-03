import pandas
import matplotlib
import matplotlib.pyplot as plt


avi_df = pandas.read_csv('avi_results.csv', index_col=0, parse_dates=True, header=None)
avi_df.rename(columns={1: 'avi'}, inplace=True)
lvm_df = pandas.read_csv('lvm_results.csv', index_col=0, parse_dates=True, header=None)
lvm_df.rename(columns={1: 'lvm'}, inplace=True)

matplotlib.rcParams.update({'font.size': 30})

all_results = pandas.concat([avi_df, lvm_df], axis=1)
# summary_bytes = 0
matplotlib.style.use('ggplot')
# print(all_results.describe())
plt.title("Wykres pudelkowy rozmiaru plikow avi oraz lvm")
plt.xlabel("Typ pliku")
plt.ylabel("Rozmiar pliku [bajty]")
all_results.describe().to_csv('sizes_summary.csv', float_format='%.0f')
all_results.boxplot()
plt.show()

# lvm_sum = 0
# avi_sum = 0
# for row in all_results.itertuples():
#     lvm_sum += row.lvm
#     avi_sum += row.avi

# print('Avi bytes: {} B'.format(avi_sum)) # bytes
# print('Lvm bytes: {} B'.format(lvm_sum)) # bytes
# print('Avi size: {} kB'.format(avi_sum / 1000)) # bytes
# print('Lvm size: {} kB'.format(lvm_sum / 1000)) # bytes
# timeframe = 30 * 24 * 60 * 60 # days-hours-minutes-seconds
# print('Time in seconds: {}'.format(timeframe))
# b_sum = lvm_sum + avi_sum # bytes
# kb_sum = avi_sum / 1000 + lvm_sum / 1000
# print('Summary bytes: {}'.format(b_sum))
# print('Summary: {} kB'.format(kb_sum))
# stream = b_sum / timeframe
# print('Stream: {} B/s'.format(stream))
# kb_stream = kb_sum / timeframe
# print('Stream: {} kB/s'.format(kb_stream))
# print('Files generated: {}'.format(all_results.shape[0]))
# mean_interval = timeframe / all_results.shape[0]
# print('Mean interval: {} s'.format(mean_interval))
# max_size = 12 * mean_interval
# print('Max possible size: {} kB'.format(max_size))
# real_size = kb_stream * mean_interval
# print('Real size: {} kB'.format(real_size))
# print('Required compression level: {} %'.format(max_size / real_size * 100))
# means = all_results.mean()
# avi_mean = means.avi / 1000
# lvm_mean = means.lvm / 1000
# sum_mean = avi_mean + lvm_mean
# print('mean avi file size: {} kB'.format(avi_mean))
# print('mean lvm file size: {} kB'.format(lvm_mean))
# print('Mean package size: {} kB'.format(sum_mean))
