import numpy as np
import pathlib as pl
import io

from . import wavelet_commons as wcom
from . import wavelet_encoder as wenc
from . import wavelet_decoder as wdec

params = wcom.WaveletParams()


def encode_file(file_name):
    data = np.loadtxt(file_name)[:, 1:]

    channels = data.shape[1]

    # Packing
    packed_measurements = bytearray()
    for channel in range(channels):
        signal = data[:, channel]
        encoded_signal, _ = wenc.signal_encode(signal, params)
        packed_measurements += len(encoded_signal).to_bytes(length=3, byteorder='big')
        packed_measurements += encoded_signal

    return packed_measurements


def encode_file_return_bytestreams(file_name):
    data = np.loadtxt(file_name)[:, 1:]

    channels = data.shape[1]

    result_data = []
    for channel in range(channels):
        signal = data[:, channel]
        encoded_signal, _ = wenc.signal_encode(signal, params)
        result_data.append(encoded_signal)
        # storage_representation = bytearray()
        # storage_representation += len(encoded_signal).to_bytes(length=2, byteorder='big')
        # storage_representation += encoded_signal
        # result_data.append(storage_representation)

    return result_data


def decode_signal_from_file(file: pl.Path):
    packed_signal = file.read_bytes()

    return wdec.decode_signal(packed_signal, params)


def decode_binary(packed_measurements):
    ptr = 0
    len_ = len(packed_measurements)
    decoded_mesaruement = []
    while ptr != len_:
        signal_len = int.from_bytes(packed_measurements[ptr:ptr + 3], byteorder='big')
        ptr += 3
        encoded_signal = packed_measurements[ptr:ptr + signal_len]
        ptr += signal_len
        decoded_signal = wdec.decode_signal(encoded_signal, params)
        decoded_mesaruement.append(decoded_signal)

    decoded_mesaruement = np.array(decoded_mesaruement).transpose()
    return decoded_mesaruement


def decode_with_indexing(packed_measurements):
    decoded_measurements = decode_binary(packed_measurements)
    len_ = decoded_measurements.shape[0]
    # original numbering is for some reason multiplied by 10e-5
    indices = np.arange(len_) / 10e3
    # transpose indices
    indices.shape = (len_, 1)
    # concatenate it with results
    data_array = np.hstack((indices, decoded_measurements))
    return data_array


def decode_to_bytestream(packed_measurements, fmt='%.6f', delimiter='\t'):
    data_array = decode_with_indexing(packed_measurements)
    outstream = io.BytesIO()

    np.savetxt(outstream, data_array, fmt=fmt, delimiter=delimiter)

    return outstream.getbuffer()


def decode_to_file(file: pl.Path, packed_measurements, fmt='%.6f', delimiter='\t'):
    decoded_measurements = decode_binary(packed_measurements)
    len_ = decoded_measurements.shape[0]
    # original numbering is for some reason multiplied by 10e-5
    indices = np.arange(len_) / 10e5
    # transpose indices
    indices.shape = (len_, 1)
    # concatenate it with results
    data_array = np.hstack((indices, decoded_measurements))
    np.savetxt(str(file), data_array, fmt=fmt, delimiter=delimiter)
