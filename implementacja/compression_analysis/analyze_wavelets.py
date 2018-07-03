import pandas as pd
import numpy as np
import pathlib as pl
import matplotlib
import matplotlib.pyplot as plt
import sys

from sync.compressors import wavelet


def decompress_and_plot(path, case_name):
    original_data = np.loadtxt(str(path))[:, 1:]
    compressed = wavelet.wavelet_lvm.encode_file(str(path))
    decompressed_data = wavelet.wavelet_lvm.decode_binary(compressed)

    plot_signals(original_data, decompressed_data, case_name)


def plot_signals(original_data, decompressed_data, case_name):
    assert original_data.shape == decompressed_data.shape

    for i in range(original_data.shape[1]):
        client_signal = original_data[:, i]
        server_signal = decompressed_data[:, i]

        plt.plot(client_signal, label='sygnal oryginalny')
        plt.plot(server_signal, label='sygnal zdekompresowany')
        plt.legend()
        plt.title('{} - kanal {}'.format(case_name, i))
        plt.xlabel('Indeks probki')
        plt.ylabel('Wartosc sygnalu')
        plt.grid()
        plt.show()


def main():
    if len(sys.argv) > 1:
        root_path = sys.argv[1]
    else:
        root_path = 'wavelet_measurements.csv'

    column_names = [
        'nazwa pliku',
        'kanal 1', 'kanal 2', 'kanal 3', 'kanal 4', 'kanal 5', 'kanal 6',
        'mean1', 'mean2', 'mean3', 'mean4', 'mean5', 'mean6'
    ]
    df = pd.read_csv(root_path, names=column_names)

    stddf = df[column_names[1:7]]

    stats = stddf.describe()
    stats.to_csv('wavelet_compression_summary.csv', float_format='%.6f')

    matplotlib.style.use('ggplot')
    stats.boxplot()
    plt.title('Wykres pudelkowy bledu sredniokwadratowego kompresji falkowej')
    plt.xlabel('Kanal pomiaru')
    plt.ylabel('Wartosc bledu')
    plt.show()

    # max_mean_column = stddf.max().argmax()
    # max_row_index = stddf[max_mean_column].argmax()
    # file_name = df.iloc[max_row_index]['nazwa pliku']
    file_name = df.sample(3)['nazwa pliku'].iloc[0]

    # min_row_index =  stddf[max_mean_column].argmin()
    # file_name = df.iloc[min_row_index]['nazwa pliku']

    # decompress_and_plot(pl.Path('../client_storage/R2017_10_06').joinpath(file_name), str(file_name))

if __name__ == '__main__':
    main()
