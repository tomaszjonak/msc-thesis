import wavelet_lvm as wl
import matplotlib.pyplot as plt
import numpy as np

file = 'dane_2f/M170614_161008.lvm'
data = np.loadtxt('dane_2f/M170614_161008.lvm')[:, 1:]

encoded = wl.encode_file(file)
decoded = wl.decode_binary(encoded)


for chan in range(decoded.shape[1]):
    plt.plot(data[:, chan], label='original')
    plt.plot(decoded[:, chan], label='decoded')
    plt.legend()
    plt.show()

mses_ = ((decoded - data)**2).mean(axis=0)
mses = mses_ / np.abs(data).max(axis=0)
print(mses)
