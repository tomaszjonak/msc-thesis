import pywt
import numpy as np
import pathlib as pl

import wavelet_commons as wcom


def signal_encode(signal, params):
    xa, xd = fdwt(signal, params)
    xa, xd, nz = qdwt(xa, xd, params)
    bs, ka, kd = encode(xa, xd, params)

    stream_with_length = add_length_to_stream(bs, len(signal))
    padded_stream = pad_stream(stream_with_length)

    return padded_stream


def add_length_to_stream(bitstream, signal_len):
    outstream = format(signal_len, 'b')
    outstream += bitstream
    return outstream


def pad_stream(bitstream):
    N = len(bitstream)
    padding_len = np.ceil(N / 8).astype(int) * 8 - N
    bitstream += '0' * padding_len
    return bitstream


def fdwt(signal, params):
    N = signal.size
    n = params.decomposition_level
    padding = np.zeros(int(np.ceil(N/2**n) * (2**n) - N))
    xa = np.concatenate((signal, padding))

    xa, *xd = pywt.wavedec(xa, 'sym4', 'per', level=n)

    return np.array(xa), np.array((*reversed(xd),))


def qdwt(xa, xd, params):
    e = np.sum(np.square(xa))

    for xd_ in xd:
        e += np.sum(np.square(xd_))

    # note that matlab round(0.5) = 1
    # while python round(0.5) = 0
    xa_ = np.around(xa / params.q) * params.q
    nz = np.count_nonzero(xa_)

    xd_ = [np.round(x_ / params.q) * params.q for x_ in xd]
    nz += np.sum(np.count_nonzero(x_) for x_ in xd_)

    return xa_, xd_, nz


def encode(xa, xd, params):
    p = 0

    ka = k_opt(xa, params)
    kd = [k_opt(x_, params) for x_ in xd]

    N, A = 0, 0

    L = len(xd)
    v = np.zeros(2**L)
    # Another magic numbers
    kod = np.zeros((10000, 5))
    for k in range(xa.size):
        v[0] = xa[k]
        d = 1

        for n in reversed(range(L)):
            v[list(range(d, 2*d))] = xd[n][list(range(d*k, d * (k + 1)))]
            d *= 2

        if params.k_max:
            ka = wcom.k_get(N, A, params.k_max)
            N, A = wcom.NA(N, A, v[0], params.N0, params.A_MAX)

        kod, p = enc_vect(v, kod, p, ka, kd, params)

    kod = kod[:p, :]

    bs = cw2bs(kod[:, -2], kod[:, -1])
    return bs, ka, kd


def k_opt(xa, params):
    nz = xa[np.nonzero(xa)]

    k_min = 0
    if not nz.size:
        return k_min

    cn_min = nz.size * 16

    for k in range(0, 4):
        CN = 0
        for u in nz:
            v = gmap1(u)

            # is this hardcoded 6 related to params.ESC_Z?
            cw, cn = GR0(v, k, params.ESC_Q, 6)
            CN += cn

        if CN < cn_min:
            cn_min = CN
            k_min = k

    return k_min


def gmap1(x):
    if x > 0:
        return 2 * x - 1

    if x < 0:
        return 2 * (abs(x) - 1)
    # not sure why theres list instead of 0 in orignal code
    return []


def GR0(v, k, ESC_Q, ESC_B):
    k = max(k, 0)
    q = v // 2**k
    r = v % (2**k)

    if q < ESC_Q:
        c = (2**q - 1) * 2**(1 + k) + r
        n = q + 1 + k
        return c, n

    if ESC_B == -1:
        msb = int(np.log2(v))

        u = v - 2**msb
        c = (2**ESC_Q - 1) * 2**(msb + 3) + (msb + 3) * 2**msb + u
        # is this hardcoded 8 ESC_Q?
        n = msb + 3 + 8

        return c, n

    c = (2**ESC_Q - 1) * 2**ESC_B + v
    n = ESC_Q + ESC_B

    return c, n


def enc_vect(V, kod, p, ka, kd, params):
    if np.count_nonzero(V) == 0:
        kod[p, :] = [1, 0, params.k_z, 0, 1]
        p += 1
        return kod, p

    nz = 0
    u = 0
    n = 0
    for n in range(V.size):
        u = V[n]

        nz += 1
        if not u:
            continue

        cw, cn = GR0(nz, params.k_z, params.ESC_Q, params.ESC_Z)

        kod[p, :] = [0, nz, params.k_z, cw, cn]
        p += 1
        k_v = 0
        nz = 0
        v = gmap1(u)

        if n == 0:
            if params.a_enc == 'vli':
                bits = 1 + np.floor(np.log2(np.absolute(u)))
                v = u
                if u < 0:
                    v = np.absolute(u) - 2**(bits - 1)
                cw = bits * 2**bits + v
                cn = 4 + bits
            elif params.a_enc in ('gre', 'agre'):
                cw, cn = GR0(v, ka, params.ESC_Q, params.ESC_V)
        else:
            cw, cn = GR0(v, k_v, cw, cn)

        kod[p, :] = [1, u, k_v, cw, cn]
        p += 1

    if n == V.size - 1 and u == 0:
        kod[p, :] = [0, 0, 0, 0, 1]
        p += 1

    return kod, p


def cw2bs(cw, cn):
    bs = ''
    for value, bits in zip(cw.astype(int), cn.astype(int)):
        bs += '{0:0>{1}b}'.format(value, bits)

    return bs


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


def write_to_file(file, bitstream):
    if len(bitstream) % 8 != 0:
        raise RuntimeError('U dun goofed m8')

    with pl.Path(file).open('wb') as fd:
        for chunk in chunks(bitstream, 8):
            fd.write(int(chunk, 2).to_bytes(1, byteorder='big'))
