import numpy as np
import wavelet_encoder as enc
import wavelet_commons as comm
import wavelet_decoder as dec
import matplotlib.pyplot as plt

data = np.loadtxt('dane_2f/M170614_161008.lvm')[:, 1:]

channels = data.shape[1]

# Packing
params = comm.WaveletParams()
packed_measurements = bytearray()
for channel in range(channels):
    signal = data[:, channel]
    encoded_signal, _ = enc.signal_encode(signal, params)
    packed_measurements += len(encoded_signal).to_bytes(length=3, byteorder='big')
    packed_measurements += encoded_signal


# Unpacking
ptr = 0
len_ = len(packed_measurements)
decoded_mesaruement = []
while ptr != len_:
    signal_len = int.from_bytes(packed_measurements[ptr:ptr+3], byteorder='big')
    ptr += 3
    encoded_signal = packed_measurements[ptr:ptr+signal_len]
    ptr += signal_len
    decoded_signal = dec.decode_signal(encoded_signal, params)
    decoded_mesaruement.append(decoded_signal)

decoded_mesaruement = np.array(decoded_mesaruement).transpose()


for chan in range(decoded_mesaruement.shape[1]):
    plt.plot(data[:, chan], label='original')
    plt.plot(decoded_mesaruement[:, chan], label='decoded')
    plt.legend()
    plt.show()

mses_ = ((decoded_mesaruement - data)**2).mean(axis=0)
mses = mses_ / np.abs(data).max(axis=0)
print(mses)
