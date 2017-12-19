import numpy as np
import pywt

from . import wavelet_commons as wcom


def decode_signal(signal, params):
    binstream = _bytestream_to_bs(signal)
    length, bs = _extract_length(binstream)

    ca, ct = _decode(bs, length, params)
    signal = iwt(ca, ct, length)

    return signal


def _decode(bs, Nx, params):
    n_levels = params.decomposition_level

    len_xa = np.ceil(Nx / 2**n_levels).astype(int)

    xa = np.zeros(len_xa)

    xd_lens = (len_xa * 2**i for i in range(0, n_levels))
    xd = list(reversed([np.zeros(ll) for ll in xd_lens]))

    N, A = 0, 0

    VN = 2**n_levels
    p = 0
    bs_len = len(bs)

    ka = 0

    for k in range(len_xa):
        if params.k_max:
            ka = wcom.k_get(N, A, params.k_max)

        v, p = _dec_vect(bs, p, VN, ka, params)

        if params.k_max:
            N, A = wcom.NA(N, A, v[0], params.N0, params.A_MAX)

        xa[k] = v[0]
        for i, xd_ in enumerate(reversed(xd)):
            d = 2**i
            xd_[d*k:d*(1+k)] = v[d:2*d]

    return xa, xd


def _dec_vect(bs, p, N, ka, params):
    n = 0
    V = np.zeros(N)

    while n < N:
        nz, p = wcom.dGR0(bs, p, 0, params.ESC_Q, params.ESC_Z)
        if not nz:
            return V, p

        n += nz

        if n == 1:
            if params.a_enc == 'vli':
                bits = int(bs[p:p + 4], 2)
                p += 4
                u = 0
                if bits:
                    u = int(bs[p:p+bits], 2)
                    p += bits

                if u < 2**(bits - 1):
                    u = -(u + 2**(bits - 1))
            elif params.a_enc in ('gre', 'agre'):
                v, p = wcom.dGR0(bs, p, ka, params.ESC_Q, params.ESC_V)
                u = gdmap1(v)
        else:
            v, p = wcom.dGR0(bs, p, params.k_v, params.ESC_Q, params.ESC_V)
            u = gdmap1(v)
        # some iffy indexing here, need algorithm spec to find out why
        V[n - 1] = u

    return V, p


def _extract_length(binstream):
    length = int(binstream[:14], 2)
    bs = binstream[14:]
    return length, bs


def _bytestream_to_bs(bytestream):
    return ''.join('{:08b}'.format(uint8) for uint8 in bytestream)


def gdmap1(z):
    if z % 2:
        x = (z + 1) / 2
    else:
        x = -(z / 2 + 1)

    return x


def iwt(xa, xd, N, wname='sym4', mode='per'):
    signal = xa
    for cdn in reversed(xd):
        signal = pywt.idwt(signal, cdn, wavelet=wname, mode=mode)

    return signal[:N]
