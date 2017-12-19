import wavelet_encoder as wenc
import wavelet_commons as wcom
import pathlib as pl
import numpy as np

plain = pl.Path('dane_2f/M170614_161008.lvm')
data = np.loadtxt(plain)

# Pierwsza kolumna zawiera nr probki
work_data = data[:, 1:]

params = wcom.WaveletParams()
channels = work_data.shape[1]

storage_path = pl.Path('python_results')
storage_path.mkdir(exist_ok=True, parents=True)

file_name_base = '{}_chan'.format(plain.with_suffix('').name)
file_name_format = file_name_base + '{}.bin'

for channel in range(channels):
    signal = work_data[:, channel]
    encoded_signal, bit_size = wenc.signal_encode(signal, params)

    bps = bit_size / signal.size
    print('Signal {}: bps {:4f}, encoded size {} bits'.format(channel, bps, bit_size))

    destination_path = storage_path.joinpath(file_name_format.format(channel))
    destination_path.write_bytes(encoded_signal)
