import pywt
import numpy as np


def make_dwt_impl(wavelet_type='sym4', wavelet_mode='per'):
    def dwt_impl(signal_):
        return pywt.dwt(signal_, wavelet_type, mode=wavelet_mode)
    return dwt_impl


def make_idwt_impl(wavelet_type='sym4', wavelet_mode='per'):
    def idwt_impl(ca, cd):
        return pywt.idwt(ca, cd,wavelet_type,wavelet_mode)
    return idwt_impl


class WaveletParams(object):
    def __init__(self):
        self.k_z = 0
        self.k_v = 0
        self.ESC_Q = 8
        self.ESC_Z = 6
        self.ESC_V = -1
        self.k_max = 3
        self.N0 = 2
        self.A_MAX = 512
        self.a_enc = 'vli'
        # Typ transformaty
        self.wname = 'sym4'
        # Paramter kompresji (nie wiadomo dokladnie co to)
        self.q = 1
        self.dwt = make_dwt_impl()
        self.idwt = make_idwt_impl()
        self.decomposition_level = 6


def k_get(N, A, k_max):
    return np.argwhere(2**np.arange(k_max+1) * N <= A).size


def NA(N, A, v, N0, A_MAX):
    if N0 == 1:
        N = 1
        A = abs(v)
        return N, A

    N += 1
    A += abs(v)

    A = min(A, A_MAX)

    if N == N0:
        N //= 2
        A //= 2

    return N, A


def dGR0(bs, p, k, ESC_Q, ESC_B):
    n = 0
    while bs[p] == '1':
        n += 1
        p += 1
        if n != ESC_Q:
            continue

        if ESC_B == -1:
            msb = int(bs[p:p+3], 2) + 3
            p += 3
            u = int(bs[p:p + msb], 2)
            p += msb
            x = u + 2**msb
        else:
            x = int(bs[p:p + ESC_B], 2)
            p += ESC_B
        return x, p

    p += 1
    r = 0
    if k:
        r = int(bs[p:p + k], 2)
    p += k
    x = n * 2**k + r

    return x, p
