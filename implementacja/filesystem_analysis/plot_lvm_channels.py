import pathlib as pl
import matplotlib.pyplot as plt
import numpy as np

test_measurement = pl.Path('../client_storage/R2017_10_06/M171006_004227.lvm')

data = np.loadtxt(test_measurement.as_posix())

plots = data.shape[1] - 1
f, axarr = plt.subplots(plots, sharex=True)

# for i, column in enumerate(data.T[1:]):
#     plt.plot(data[:, 0]*1000, column, label='Kanal {}'.format(i))
# plt.grid()
# plt.legend()
for i, column in enumerate(data.T[1:]):
    axarr[i].plot(data[:, 0]*1000, column, label='Sygnal w kanale {}'.format(i))
    axarr[i].legend(loc='center right')
    # axarr[i].grid()
    # axarr[i].set_title('Sygnal {}'.format(i))

plt.xlim([data[0, 0]*1000, data[-1, 0]*1000])
plt.show()