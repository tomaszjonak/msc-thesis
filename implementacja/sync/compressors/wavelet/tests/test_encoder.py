import pytest
import hashlib
import numpy as np
import pathlib as pl
from scipy import io as scio

from .. import wavelet_encoder
from .. import wavelet_commons
from .. import wavelet_lvm

"""
This file uses reference output from matlab implementation to test python
"""

bad_file = 'wavelet/tests/M171006_183622.lvm'


def test_fdwt2(fdwt_matlab_state, params):
    input_x, expected_xa, expected_xd = fdwt_matlab_state

    xa, xd = wavelet_encoder.fdwt(input_x, params)

    assert np.allclose(xa, expected_xa, atol=1e-16)
    for xd_el, dwt_xd_el in zip(xd, expected_xd):
        assert np.allclose(xd_el, dwt_xd_el, atol=1e-16)


def test_qdwt2(qdwt_matlab_state, params):
    input_xa, input_xd, input_q, expected_xa, expected_xd, expected_nz = qdwt_matlab_state
    assert params.q == input_q

    xa, xd, nz = wavelet_encoder.qdwt(input_xa, input_xd, params)

    assert np.array_equal(xa, expected_xa)

    for xd_el, expected_xd_el in zip(xd, expected_xd):
        # assert xd_el.shape == expected_xd_el.shape
        assert np.array_equal(xd_el, expected_xd_el)

    assert nz == expected_nz


def test_encv32(encv3_matlab_state, params):
    input_xa, input_xd, expected_bs, expected_ka, expected_kd = encv3_matlab_state

    bs, ka, kd = wavelet_encoder.encode(input_xa, input_xd, params)

    assert expected_bs == bs
    assert expected_ka == ka
    assert np.array_equal(expected_kd, kd)


def test_kopt2(kopt_matlab_state, params):
    expected_ka, expected_kd, input_xa, input_xd = kopt_matlab_state

    ka = wavelet_encoder.k_opt(input_xa, params)
    assert expected_ka == ka

    kd = [wavelet_encoder.k_opt(element, params) for element in input_xd]
    for expected_element, element in zip(expected_kd, kd):
        assert expected_element == element


def test_kget2(kget_matlab_state):
    expected_ka, input_N, input_A, input_kmax = kget_matlab_state

    ka = wavelet_commons.k_get(input_N, input_A, input_kmax)
    assert expected_ka == ka


def test_na2(na_matlab_state):
    input_N, input_A, input_v1, input_N0, input_AMAX, expected_N, expected_A = na_matlab_state

    result_N, result_A = wavelet_commons.NA(input_N, input_A, input_v1, input_N0, input_AMAX)

    assert result_N == expected_N
    assert result_A == expected_A


def test_enc_vect2(enc_vect_matlab_state, params):
    input_v, input_kod, input_p, input_ka, input_kd, expected_kod, expected_p = enc_vect_matlab_state

    kod, p = wavelet_encoder.enc_vect(input_v, input_kod, input_p, input_ka, input_kd, params)

    assert np.array_equal(expected_kod, kod)
    assert expected_p == p


def test_cw2bs2(cw2bs_matlab_state):
    input_kod, expected_bs = cw2bs_matlab_state

    bs = wavelet_encoder.cw2bs(input_kod[:, 3], input_kod[:, 4])
    assert expected_bs == bs


def test_fdwt(fdwt):
    expected_xa = scio.loadmat('wavelet/tests/signal_data/channel1/dwt_results.mat')['xa'][0]
    expected_xd = scio.loadmat('wavelet/tests/signal_data/channel1/dwt_xd_results.mat')['xd'][0]

    xa, xd = fdwt

    assert np.allclose(xa, expected_xa, atol=1e-16)

    for xd_el, dwt_xd_el in zip(xd, expected_xd):
        assert np.allclose(xd_el, dwt_xd_el, atol=1e-16)


def test_qdwt(qdwt):
    qdwt_state = scio.loadmat('wavelet/tests/signal_data/channel1/qdwt_results.mat')
    expected_xa = qdwt_state['xa'][0]
    expected_xd = qdwt_state['xd'][0]
    expected_nz = qdwt_state['nz'][0][0]

    xa, xd, nz = qdwt

    assert np.allclose(xa, expected_xa, atol=1e-16)

    for xd_el, expected_xd_el in zip(xd, expected_xd):
        # assert xd_el.shape == expected_xd_el.shape
        assert np.allclose(xd_el, expected_xd_el, atol=1e-16)

    assert nz == expected_nz


def test_kopt(qdwt, params):
    xa, xd, _ = qdwt
    ka = wavelet_encoder.k_opt(xa, params)
    assert ka == 0

    expected = [0, 0, 0, 0, 0, 0]
    got = []
    for xd_elem in xd:
        got.append(wavelet_encoder.k_opt(xd_elem, params))
    assert expected == got


def test_kget(kget_params):
    expected_ka, input_N, input_A, input_kmax = kget_params

    assert expected_ka == wavelet_commons.k_get(input_N, input_A, input_kmax)


def test_na(kget_params):
    _, input_N, input_A, _ = kget_params

    expected_N = 1
    expected_A = 0
    input_v1 = 0
    input_N0 = 2
    input_AMAX = 512

    result_N, result_A = wavelet_commons.NA(input_N, input_A, input_v1, input_N0, input_AMAX)
    assert result_N == expected_N
    assert result_A == expected_A


# @pytest.mark.parametrize("test_input,expected", [
#     ((1, params.k_z, params.ESC_Q, params.ESC_V), (2, 2)),
#     ((0, params.k_v, params.ESC_Q, params.ESC_V), (0, 1)),
# ])
# def test_gr0(test_input, expected):
#     nz, k_z, esc_q, esc_z = test_input
#     expected_cw, expected_cn = expected
#
#     got_cw, got_cn = wavelet_encoder.GR0(nz, k_z, esc_q, esc_z)
#
#     assert expected_cw == got_cw
#     assert expected_cn == got_cn


def test_gmap1():
    u = -1
    expected_v = 0
    got_v = wavelet_encoder.gmap1(u)
    assert expected_v == got_v


def test_enc_vec(pre_enc_vec, post_enc_vec, params):
    v, input_kod, input_p, ka, kd = pre_enc_vec
    expected_kod, expected_p = post_enc_vec

    got_kod, got_p = wavelet_encoder.enc_vect(v, input_kod, input_p, ka, kd, params)
    assert np.array_equal(expected_kod, got_kod)
    assert expected_p == got_p


def test_cw2bs():
    cw2bs_state = scio.loadmat('wavelet/tests/signal_data/channel1/cw2bs_state.mat')
    kod = cw2bs_state['kod']
    expected_bs = cw2bs_state['bs'][0]

    got_bs = wavelet_encoder.cw2bs(kod[:, 3], kod[:, 4])
    assert expected_bs == got_bs


def test_encodev3(encv3):
    encv3_state = scio.loadmat('wavelet/tests/signal_data/channel1/encv3_results.mat')
    expected_bs = encv3_state['bs'][0]
    expected_ka = encv3_state['ka'][0][0]
    expected_kd = encv3_state['kd'][0]

    bs, ka, kd = encv3

    assert expected_bs == bs
    assert expected_ka == ka
    assert np.array_equal(expected_kd, kd)


def md5(fname: pl.Path):
    hash_md5 = hashlib.md5()
    with fname.open("rb") as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def test_end_to_end():
    python_path = pl.Path('wavelet/tests/python_compressed')
    matlab_path = pl.Path('wavelet/tests/matlab_compressed')
    python_path.mkdir(parents=True, exist_ok=True)

    bytestreams = wavelet_lvm.encode_file_return_bytestreams(bad_file)

    results = []
    for i, bytestream in enumerate(bytestreams):
        signal_path = python_path.joinpath('{}_{}_{}.wavelet'.format(pl.Path(bad_file).name, 'sym4', i + 1))
        signal_path.write_bytes(bytestream)
        results.append(signal_path)

    for file in (signal_path.name for signal_path in results):
        python_file = python_path.joinpath(file)
        matlab_file = matlab_path.joinpath(file)
        assert md5(python_file) == md5(matlab_file), str(python_file)


def test_loop_na(loop_na_params):
    input_N, input_A, input_v1, input_N0, input_AMAX, expected_N, expected_A = loop_na_params

    result_N, result_A = wavelet_commons.NA(input_N, input_A, input_v1, input_N0, input_AMAX)

    assert result_N == expected_N
    assert result_A == expected_A


def test_loop_enc_vec(loop_enc_vec_params, params):
    input_v, input_kod, input_p, input_ka, input_kd, expected_kod, expected_p = loop_enc_vec_params

    kod, p = wavelet_encoder.enc_vect(input_v, input_kod, input_p, input_ka, input_kd, params)

    # assert np.array_equal(expected_kod, kod)
    for i in range(kod.shape[0]):
        if not np.array_equal(expected_kod[i], kod[i]):
            assert False
    assert expected_p == p


def test_another_gr0():
    v = 3
    k_v = 0
    ESC_Q = 8
    ESC_V = -1

    cw, cn = wavelet_encoder.GR0(v, k_v, ESC_Q, ESC_V)

    expected_cw = 14
    expected_cn = 4

    assert expected_cw == cw
    assert expected_cn == cn
