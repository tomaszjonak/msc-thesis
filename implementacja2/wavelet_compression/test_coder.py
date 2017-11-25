import wavelet_coder as wvc
import pathlib as pl
import numpy as np

plain = pl.Path('dane_2f/M170614_161008.lvm')
compressed_channels = pl.Path('bs').glob('*')

data = np.loadtxt(plain)

usefull_columns = list(range(1, data.shape[1]))

# Pierwsza kolumna zawiera nr probki
work_data = data[:, 1:]

params = wvc.WaveletParams()
channels = work_data.shape[1]

storage_path = pl.Path('python_results')
storage_path.mkdir(exist_ok=True, parents=True)

file_name_base = '{}_chan'.format(plain.with_suffix('').name)
file_name_format = file_name_base + '{}.bin'

for channel in range(channels):
    signal = work_data[:, channel]
    encoded_signal = wvc.signal_encode(signal, params)

    bit_size = len(encoded_signal)
    bps = bit_size / signal.size
    print('Signal {}: bps {:4f}, encoded size {} bits'.format(channel, bps, bit_size))

    destination_path = storage_path.joinpath(file_name_format.format(channel))
    wvc.write_to_file(destination_path, encoded_signal)
