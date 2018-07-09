import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt


def switch_to_percents(ndarray):
    base_sizes = ndarray[:,0]
    base_sizes.shape = (base_sizes.shape[0], 1)

    data = ndarray[:,1:]
    return data / base_sizes * 100


def describe_lvm():
    lvm_data = np.loadtxt('lvm_results.csv', skiprows=1, usecols=[1,2,3,4,5], delimiter=',', dtype=int)
    lvm_percents = pd.DataFrame(switch_to_percents(lvm_data))
    lvm_percents.rename({0: 'lzma', 1: 'bz2', 2: 'zlib', 3: 'wavelets'}, axis='columns', inplace=True)
    lvm_description = lvm_percents.describe()
    print(lvm_description)
    lvm_description.to_csv('lvm_compression_summary.csv', float_format='%.2f')
    matplotlib.style.use('ggplot')
    lvm_percents.boxplot(return_type='axes', fontsize=20)
    plt.title('Wykres pudelkowy wielkosci skompresowanego pliku lvm dla badanych metod kompresji', fontsize=20)
    plt.xlabel("Algorytm kompresji", fontsize=20)
    plt.ylabel("Sprawnosc kompresji [procent wielkosci oryginalnego pliku]", fontsize=20)
    plt.show()


def describe_avi():
    avi_data = np.loadtxt('avi_results.csv', skiprows=1, usecols=[1,2,3,4,5], delimiter=',', dtype=int)
    avi_percents = pd.DataFrame(switch_to_percents(avi_data))
    avi_percents.rename({0: 'lzma', 1: 'bz2', 2: 'zlib', 3: 'x264'}, axis='columns', inplace=True)
    avi_description = avi_percents.describe()
    print(avi_description)
    avi_description.to_csv('lvm_compression_summary.csv', float_format='%.2f')
    matplotlib.style.use('ggplot')
    avi_percents.boxplot(return_type='axes', fontsize=20)
    plt.title('Wykres pudelkowy wielkosci skompresowanego pliku avi dla badanych metod kompresji', fontsize=20)
    plt.xlabel("Algorytm kompresji", fontsize=20)
    plt.ylabel("Sprawnosc kompresji [procent wielkosci oryginalnego pliku]", fontsize=20)
    plt.show()


def main():
    x = input('Describe lvm? ')
    if x:
        describe_lvm()

    x = input('Describe avi? ')
    if x:
        describe_avi()

main()
