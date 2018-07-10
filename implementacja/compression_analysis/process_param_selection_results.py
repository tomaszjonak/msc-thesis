import matplotlib
import matplotlib.pyplot as plt
import pandas

data = pandas.read_csv('x264_params.csv')

data['percent_of_original'] = (data['compressed_size'] / data['original_size']) * 100

result = data.groupby('preset')['percent_of_original', 'compression_time']

compression_df = pandas.DataFrame()
times_df = pandas.DataFrame()
for name, df in result:
    # print(name)
    # print(df.reset_index()['percent_of_original'])
    compression_df[name] = df.reset_index()['percent_of_original']
    times_df[name] = df.reset_index()['compression_time']

column_order = [
    'ultrafast',
    'superfast',
    'veryfast',
    'faster',
    'fast',
    'medium',
    'slow',
    'slower',
    'veryslow',
]

compression_df = compression_df[column_order]
times_df = times_df[column_order]

matplotlib.style.use('ggplot')
# matplotlib.rcParams.update({'font.size': 18})
# print(compression_df.describe())
# print(times_df.describe())
# fig, axes = plt.subplots(2, 1, sharex='col')
# plt.locator_params(nbins=20)
# compression_df.boxplot()
# summary = compression_df.describe()
# summary.to_csv('compression_summary.csv', float_format='%.2f')
# print(type(summary))
# plt.title('Wykres pudelkowy sprawnosci kompresji dla presetow programu ffmpeg')
# plt.xlabel('Preset programu ffmpeg')
# plt.ylabel('Wspolczynnik kompresji [procent wielkosci oryginalu]')
#
# plt.show()
# times_df.boxplot()
# summary = times_df.describe()
# summary.to_csv('times_summary.csv', float_format='%.2f')
# plt.title('Wykres pudelkowy czasu kompresji dla presetow programu ffmpeg')
# plt.xlabel('Preset programu ffmpeg')
# plt.ylabel('Czas kompresji [sekundy]')
# plt.show()


matplotlib.rcParams.update({'font.size': 18})
median_data = result.median()
# print(median_data)
median_data.to_csv('median_summary.csv', float_format='%.2f')
# print(mean_data.index)
# mean_data.plot.scatter('percent_of_original', 'compression_time')
path = plt.scatter(median_data['compression_time'], median_data['percent_of_original'])
for i, label in enumerate(median_data.index):
    path.axes.annotate(label, (median_data['compression_time'][i], median_data['percent_of_original'][i]),
                       va="bottom", ha="center")
plt.title('Mediana czasu kompresji do wspolczynnika kompresji w zaleznosci od parametru preset')
plt.xlabel('Czas kompresji [sekundy]')
plt.ylabel('Wspolczynnik kompresji [procent wielkosci oryginalu]')

plt.show()
