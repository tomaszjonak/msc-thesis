import wavelet_decoder as wvd
import wavelet_commons as wcom
import pathlib as pl
import numpy as np
import matplotlib.pyplot as plt

original_signal = pl.Path('dane_2f/M170614_161008.lvm')
data = np.loadtxt(original_signal)

test_original_signal = data[:, 1]

source_folder = pl.Path('bs')
source_files = list(source_folder.glob('*'))

params = wcom.WaveletParams()
for i, file in enumerate(source_files):
    test_original_signal = data[:, i + 1]
    test_encoded_signal = file.read_bytes()
    test_decoded_signal = wvd.decode_signal(test_encoded_signal, params)

    err = np.sqrt(((test_decoded_signal - test_original_signal)**2)).mean()/np.abs(test_original_signal).max() * 100
    print("{}   E: {:4f}".format(file.name, err))

    plt.plot(test_original_signal)
    plt.plot(test_decoded_signal)
    plt.grid()
    plt.show()
