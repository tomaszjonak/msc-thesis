import pathlib as pl
import numpy as np
import pandas
from pprint import pprint
import matplotlib.pyplot as plt
import matplotlib
import multiprocessing
import collections
import csv

import sys
from sync.compressors import wavelet


def calculate_mse(tpl):
    client_file, server_file = tpl
    client_data = np.loadtxt(str(client_file))[:, 1:]
    server_data = np.loadtxt(str(server_file))[:, 1:]

    wavelet_mse = []
    for i in range(client_data.shape[1]):
        client_signal = client_data[:, i]
        server_signal = server_data[:, i]
        channel_mse = np.sqrt(((server_signal - client_signal)**2)).mean()/np.abs(client_signal).max() * 100
        wavelet_mse.append(channel_mse)
    std_mse = ((client_data - server_data) ** 2).mean(axis=0)

    return np.array(wavelet_mse), std_mse, (client_file, server_file)


def measure_wavelet_compression(path: pl.Path):
    try:
        original_data = np.loadtxt(str(path))[:, 1:]
        compressed = wavelet.wavelet_lvm.encode_file(str(path))
        decompressed_data = wavelet.wavelet_lvm.decode_binary(compressed)

        wavelet_mse = []
        for i in range(original_data.shape[1]):
            client_signal = original_data[:, i]
            server_signal = decompressed_data[:, i]
            channel_mse = np.sqrt(((server_signal - client_signal)**2)).mean()/np.abs(client_signal).max() * 100
            wavelet_mse.append(channel_mse)
        std_mse = ((original_data - decompressed_data) ** 2).mean(axis=0)
    except Exception as e:
        print(e)
        return np.array([path.name] + ['' for _ in range(6)] + ['' for _ in range(6)])

    return np.hstack(([path.name], std_mse, wavelet_mse))


def main():
    if len(sys.argv) > 1:
        root_path = pl.Path(sys.argv[1])
    else:
        root_path = pl.Path('../client_storage')

    files = root_path.rglob('*.lvm')

    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    results = pool.map(measure_wavelet_compression, files)
    with open('wavelet_measurements.csv', 'w') as fd:
        writer = csv.writer(fd)
        for result in results:
            writer.writerow(result)

if __name__ == '__main__':
    main()
