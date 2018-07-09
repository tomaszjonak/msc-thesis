import pytest
import numpy as np
import pathlib as pl
import matplotlib.pyplot as plt

from .. import wavelet_lvm
from .. import wavelet_decoder


def test_bs_read(bs_read_matlab_state):
    file_bytes, expected_bs, expected_length = bs_read_matlab_state

    binstream = wavelet_decoder._bytestream_to_bs(file_bytes)
    length, bs = wavelet_decoder._extract_length(binstream)

    assert bs == expected_bs
    assert length == expected_length


def test_decv3(decv3_matlab_state, params):
    bytestream, n_levels, original_len, ka, kd, expected_xa2, expected_xd2 = decv3_matlab_state

    xa2, xd2 = wavelet_decoder._decode(bytestream, original_len, params)

    assert np.allclose(xa2, expected_xa2, atol=1e-16)
    for xd_el, dwt_xd_el in zip(xd2, expected_xd2):
        assert np.allclose(xd_el, dwt_xd_el, atol=1e-16)


def test_iwt(iwt_matlab_state):
    original_len, xa2, xd2, expected_x2 = iwt_matlab_state

    x2 = wavelet_decoder.iwt(xa2, xd2, original_len)
    assert np.allclose(x2, expected_x2)


def signal_error(sig1, sig2):
    assert sig1.shape == sig2.shape
    return np.square(sig1 - sig2).mean()


def test_decode(bad_signal_file):
    source_folder = pl.Path('wavelet/tests/matlab_compressed')

    stem = bad_signal_file.stem

    original_signals = np.loadtxt('wavelet/tests/source_signals/{}.lvm'.format(stem))[:, 1:]
    matlab_decoded_signals = np.loadtxt('wavelet/tests/matlab_compressed/{}.matlab.lvm'.format(stem))
    source_files = source_folder.glob('{}*.wavelet'.format(stem))

    matlab_errors = []
    python_errors = []
    for i, file in enumerate(source_files):
        original_signal = original_signals[:, i]
        matlab_decoded_signal = matlab_decoded_signals[:, i]
        python_decoded_signal = wavelet_lvm.decode_signal_from_file(file)

        err_matlab_original = signal_error(original_signal, matlab_decoded_signal)
        err_python_original = signal_error(original_signal, python_decoded_signal)
        err_matlab_python = signal_error(matlab_decoded_signal, python_decoded_signal)
        matlab_errors.append(err_matlab_original)
        python_errors.append(err_python_original)
        assert err_matlab_python < 10e-6
        # error_pairs.append((err_matlab_original, err_python_original))

        # assert

        # print("{}   matlab: {:4f}".format(file.name, err_matlab_original))
        # print("{}   python: {:4f}".format(file.name, err_python_original))
        # print("{}   diff:   {:4f}".format(file.name, err_matlab_python))

        # plt.plot(original_signal, label='original')
        # plt.plot(matlab_decoded_signal, label='matlab')
        # plt.plot(python_decoded_signal, label='python')
        # plt.ylabel('Wartosc sygnalu')
        # plt.xlabel('Probka')
        # plt.grid()
        # plt.legend()
        # plt.show()

    assert np.allclose(matlab_errors, python_errors)
