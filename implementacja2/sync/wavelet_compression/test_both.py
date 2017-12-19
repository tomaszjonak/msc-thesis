import wavelet_encoder as wenc
import wavelet_decoder as wdec
import wavelet_commons as wcom

import matplotlib.pyplot as plt
import pathlib as pl
import numpy as np

plain = pl.Path('dane_2f/M170614_161008.lvm')
data = np.loadtxt(plain)

work_data = data[:, 1:]

params = wcom.WaveletParams()
channels = work_data.shape[1]

destination_folder = pl.Path('bs')

for channel in range(channels):
    original_signal = work_data[:, channel]
    encoded_signal, _ = wenc.signal_encode(original_signal, params)
    destination_folder.joinpath('chan_{}.bin'.format(channel)).write_bytes(encoded_signal)

    decoded_signal = wdec.decode_signal(encoded_signal, params)

    err = np.sqrt(((decoded_signal - original_signal)**2)).mean()/np.abs(original_signal).max() * 100
    print("{}   E: {:4f}".format(channel, err))

    plt.plot(original_signal)
    plt.plot(decoded_signal)
    plt.grid()
    plt.show()

