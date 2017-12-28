import pathlib as pl
import numpy as np
import pandas
from pprint import pprint
import matplotlib.pyplot as plt
import multiprocessing
import collections


def get_file_pairs(client_storage, server_storage, extension):
    relative_paths = [path.relative_to(server_storage) for path in server_storage.rglob('*.{}'.format(extension))]
    file_pairs = [(client_storage.joinpath(path), server_storage.joinpath(path)) for path in relative_paths]
    invalid_paths = [path for _, path in file_pairs if not path.exists()]
    valid_paths = [(client_path, server_path) for client_path, server_path in file_pairs if client_path.exists()]
    return valid_paths, invalid_paths


def analyse_file_pair(client_file, server_file, case_name):
    client_data = np.loadtxt(str(client_file))[:, 1:]
    server_data = np.loadtxt(str(server_file))[:, 1:]

    if client_data.shape != server_data.shape:
        print(client_data.shape, server_data.shape)
    else:
        plot_signals(client_data, server_data, case_name)


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


def plot_signals(client_data, server_data, case_name):
    assert client_data.shape == server_data.shape

    for i in range(client_data.shape[1]):
        client_signal = client_data[:, i]
        server_signal = server_data[:, i]

        plt.plot(client_signal, label='original')
        plt.plot(server_signal, label='decoded')
        plt.legend()
        plt.title('{} - channel {}'.format(case_name, i))
        plt.grid()
        plt.show()


def main():
    client_storage = pl.Path('../client_storage')
    server_storage = pl.Path('../server_received')

    pairs, invalid_paths = get_file_pairs(client_storage, server_storage, 'lvm')
    if invalid_paths:
        pprint(invalid_paths)

    with multiprocessing.Pool() as pool:
        results = pool.map(calculate_mse, pairs)

    test_values = (
        ('wavelet_max_channels_mean', max(results, key=lambda x: x[0].mean())),
        ('wavelet_max_channels_max', max(results, key=lambda x: x[0].max())),
        ('wavelet_max_channels_sum', max(results, key=lambda x: x[0].sum())),
        ('std_max_channels_mean', max(results, key=lambda x: x[1].mean())),
        ('std_max_channels_max', max(results, key=lambda x: x[1].max())),
        ('std_max_channels_sum', max(results, key=lambda x: x[1].sum())),
        ('wavelet_min_channels_mean', min(results, key=lambda x: x[0].mean())),
        ('wavelet_min_channels_max', min(results, key=lambda x: x[0].max())),
        ('std_min_channels_mean', min(results, key=lambda x: x[1].mean())),
        ('std_min_channels_max', min(results, key=lambda x: x[1].max())),
        # TODO srednie wartosci
    )

    associations_dict = collections.defaultdict(list)
    for case, (_, _, pair) in test_values:
        associations_dict[pair].append(case)
    pprint(associations_dict)

    x = input('Print summaries? ')
    if x:
        wavelet_means = pandas.DataFrame([record[0] for record in results])
        std_means = pandas.DataFrame([record[1] for record in results])

        print('\nMean calculated as in matlab')
        print(wavelet_means.describe())
        print('\nMean in default way')
        print(std_means.describe())

    x = input('Print significant plots? ')
    if x:
        for files, cases in associations_dict.items():
            client_file, server_file = files
            analyse_file_pair(client_file, server_file, repr(cases))

    x = input('Print two random? ')
    if x:
        indices = np.random.randint(0, len(results), 2)
        test_pairs = [results[i][2] for i in indices]
        print('Checking {}'.format(str(test_pairs)))
        for i, (client_file, server_file) in enumerate(test_pairs):
            analyse_file_pair(client_file, server_file, '{}'.format(client_file.relative_to(client_storage).as_posix()))


main()
