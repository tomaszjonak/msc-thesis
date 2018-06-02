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

# print(compression_df.describe())
# print(times_df.describe())
# fig, axes = plt.subplots(2, 1, sharex='col')
matplotlib.style.use('ggplot')
plt.locator_params(nbins=20)
compression_df.boxplot()
summary = compression_df.describe()
summary.to_csv('compression_summary.csv', float_format='%.2f')
print(type(summary))
plt.title('Wykres pudelkowy sprawnosci kompresji dla presetow programu ffmpeg')
plt.xlabel('Preset programu ffmpeg')
plt.ylabel('Sprawnosc kompresji [procent wielkosci oryginalnego pliku]')
# plt.show()
times_df.boxplot()
summary = times_df.describe()
summary.to_csv('times_summary.csv', float_format='%.2f')
plt.title('Wykres pudelkowy czasu kompresji dla presetow programu ffmpeg')
plt.xlabel('Preset programu ffmpeg')
plt.ylabel('Czas kompresji [sekundy]')
# plt.show()

median_data = result.median()
print(median_data)
median_data.to_csv('median_summary.csv', float_format='%.2f')
# print(mean_data.index)
# mean_data.plot.scatter('percent_of_original', 'compression_time')
path = plt.scatter(median_data['compression_time'], median_data['percent_of_original'])
for i, label in enumerate(median_data.index):
    path.axes.annotate(label, (median_data['compression_time'][i], median_data['percent_of_original'][i]))
plt.title('Mediana czasu do sprawnosci kompresji dla presetow programu ffmpeg')
plt.xlabel('Czas kompresji [sekundy]')
plt.ylabel('Sprawnosc [procent wielkosci oryginalu]')

# plt.show()
