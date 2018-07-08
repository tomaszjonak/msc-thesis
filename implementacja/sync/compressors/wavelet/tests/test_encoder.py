import pytest
import hashlib
import numpy as np
import pathlib as pl
from .. import wavelet_encoder
from .. import wavelet_commons
from .. import wavelet_lvm


def test_fdwt(fdwt_matlab_state, params):
    input_x, expected_xa, expected_xd = fdwt_matlab_state

    xa, xd = wavelet_encoder.fdwt(input_x, params)

    assert np.allclose(xa, expected_xa, atol=1e-16)
    for xd_el, dwt_xd_el in zip(xd, expected_xd):
        assert np.allclose(xd_el, dwt_xd_el, atol=1e-16)


def test_qdwt(qdwt_matlab_state, params):
    input_xa, input_xd, input_q, expected_xa, expected_xd, expected_nz = qdwt_matlab_state
    assert params.q == input_q

    xa, xd, nz = wavelet_encoder.qdwt(input_xa, input_xd, params)

    assert np.array_equal(xa, expected_xa)

    for xd_el, expected_xd_el in zip(xd, expected_xd):
        # assert xd_el.shape == expected_xd_el.shape
        assert np.array_equal(xd_el, expected_xd_el)

    assert nz == expected_nz


def test_encv3(encv3_matlab_state, params):
    input_xa, input_xd, expected_bs, expected_ka, expected_kd = encv3_matlab_state

    bs, ka, kd = wavelet_encoder.encode(input_xa, input_xd, params)

    assert expected_bs == bs
    assert expected_ka == ka
    assert np.array_equal(expected_kd, kd)


def test_kopt(kopt_matlab_state, params):
    expected_ka, expected_kd, input_xa, input_xd = kopt_matlab_state

    ka = wavelet_encoder.k_opt(input_xa, params)
    assert expected_ka == ka

    kd = [wavelet_encoder.k_opt(element, params) for element in input_xd]
    for expected_element, element in zip(expected_kd, kd):
        assert expected_element == element


def test_kget(kget_matlab_state):
    expected_ka, input_N, input_A, input_kmax = kget_matlab_state

    ka = wavelet_commons.k_get(input_N, input_A, input_kmax)
    assert expected_ka == ka


def test_na(na_matlab_state):
    input_N, input_A, input_v1, input_N0, input_AMAX, expected_N, expected_A = na_matlab_state

    result_N, result_A = wavelet_commons.NA(input_N, input_A, input_v1, input_N0, input_AMAX)

    assert result_N == expected_N
    assert result_A == expected_A


def test_enc_vect(enc_vect_matlab_state, params):
    input_v, input_kod, input_p, input_ka, input_kd, expected_kod, expected_p = enc_vect_matlab_state

    kod, p = wavelet_encoder.enc_vect(input_v, input_kod, input_p, input_ka, input_kd, params)

    assert np.array_equal(expected_kod, kod)
    assert expected_p == p


def test_cw2bs(cw2bs_matlab_state):
    input_kod, expected_bs = cw2bs_matlab_state

    bs = wavelet_encoder.cw2bs(input_kod[:, 3], input_kod[:, 4])
    assert expected_bs == bs


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

    """
    This file uses reference output from matlab implementation to test python
    """
    bad_file = 'wavelet/tests/M171006_183622.lvm'
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
