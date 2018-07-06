from sync.compressors import wavelet
import matplotlib.pyplot as plt
import pathlib as pl
import numpy as np


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


bad_file = 'M171006_183622.lvm'
decompress_and_plot(bad_file, bad_file)