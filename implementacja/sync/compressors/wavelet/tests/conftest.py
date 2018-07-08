import pytest
import numpy as np
import pathlib as pl
from scipy import io as scio

from .. import wavelet_commons
from .. import wavelet_encoder

params = wavelet_commons.WaveletParams()
bad_file = 'wavelet/tests/M171006_183622.lvm'
data = np.loadtxt(bad_file)[:, 1:]


@pytest.fixture
def params():
    return wavelet_commons.WaveletParams()


@pytest.fixture(scope='function', params=[
    'wavelet/tests/signal_data/channel1',
    'wavelet/tests/signal_data/channel4'
])
def fdwt_matlab_state(request):
    state = scio.loadmat(request.param + '/fdwt_results.mat')
    x = state['x'][0]
    xa = state['xa'][0]
    xd = [elem[0] for elem in state['xd'][0]]
    return x, xa, xd


@pytest.fixture(scope='function', params=[
    'wavelet/tests/signal_data/channel1',
    'wavelet/tests/signal_data/channel4'
])
def qdwt_matlab_state(request):
    state1 = scio.loadmat(request.param + '/fdwt_results.mat')
    input_xa = state1['xa'][0]
    input_xd = [elem[0] for elem in state1['xd'][0]]

    state2 = scio.loadmat(request.param + '/qdwt_results.mat')
    input_q = state2['q'][0][0]
    expected_xa = state2['xa'][0]
    expected_xd = [elem[0] for elem in state2['xd'][0]]
    expected_nz = state2['nz'][0][0]

    return input_xa, input_xd, input_q, expected_xa, expected_xd, expected_nz


@pytest.fixture(scope='function', params=[
    'wavelet/tests/signal_data/channel1',
    'wavelet/tests/signal_data/channel4'
])
def encv3_matlab_state(request):
    state = scio.loadmat(request.param + '/encv3_results.mat')

    input_xa = state['xa'][0]
    input_xd = [elem[0] for elem in state['xd'][0]]

    expected_bs = state['bs'][0]
    expected_ka = state['ka'][0][0]
    expected_kd = state['kd'][0]

    return input_xa, input_xd, expected_bs, expected_ka, expected_kd


@pytest.fixture(scope='function', params=[
    'wavelet/tests/signal_data/channel4'
])
def kopt_matlab_state(request):
    state = scio.loadmat(request.param + '/kopt_results.mat')

    ka = state['ka'][0][0]
    kd = state['kd'][0]
    xa = state['xa'][0]
    xd = state['xd'][0]

    return ka, kd, xa, xd


@pytest.fixture(scope='function', params=[
    'wavelet/tests/signal_data/channel4'
])
def kget_matlab_state(request):
    state = scio.loadmat(request.param + '/kget_results.mat')

    expected_ka = state['ka'][0][0]
    input_N = state['N'][0][0]
    input_A = state['A'][0][0]
    input_kmax = state['k_max'][0][0]

    return expected_ka, input_N, input_A, input_kmax


@pytest.fixture(scope='function', params=[
    'wavelet/tests/signal_data/channel4'
])
def na_matlab_state(request):
    state = scio.loadmat(request.param + '/kget_results.mat')
    input_N = state['N'][0][0]
    input_A = state['A'][0][0]

    state = scio.loadmat(request.param + '/na_results.mat')

    input_v1 = state['v'][0][0]
    input_N0 = state['N0'][0][0]
    input_AMAX = state['A_MAX'][0][0]
    expected_N = state['N'][0][0]
    expected_A = state['A'][0][0]

    return input_N, input_A, input_v1, input_N0, input_AMAX, expected_N, expected_A


@pytest.fixture(scope='function', params=[
    'wavelet/tests/signal_data/channel4'
])
def enc_vect_matlab_state(request):
    pre_state = scio.loadmat(request.param + '/enc_pre_results.mat')

    input_v = pre_state['v'][0]
    input_kod = pre_state['kod'].astype('int64')
    input_p = pre_state['p'][0][0] - 1
    input_ka = pre_state['ka'][0][0]
    input_kd = pre_state['kd'][0]

    post_state = scio.loadmat(request.param + '/enc_post_results.mat')

    expected_kod = post_state['kod'].astype('int64')
    expected_p = post_state['p'][0][0] - 1

    return input_v, input_kod, input_p, input_ka, input_kd, expected_kod, expected_p


@pytest.fixture(scope='function', params=[
    'wavelet/tests/signal_data/channel4'
])
def cw2bs_matlab_state(request):
    state = scio.loadmat(request.param + '/cw2bs_results.mat')

    input_kod = state['kod'].astype('int64')
    expected_bs = state['bs'][0]

    return input_kod, expected_bs


@pytest.fixture
def fdwt(params):
    signal = data[:, 0]
    xa, xd = wavelet_encoder.fdwt(signal, params)

    return xa, xd


@pytest.fixture
def qdwt(fdwt, params):
    xa, xd = fdwt
    return wavelet_encoder.qdwt(xa, xd, params)


@pytest.fixture
def encv3(qdwt, params):
    xa, xd, nz = qdwt
    return wavelet_encoder.encode(xa, xd, params)


@pytest.fixture
def kopt(qdwt, params):
    xa, _, _ = qdwt
    return wavelet_encoder.k_opt(xa, params)


@pytest.fixture
def kget_params():
    kget_state = scio.loadmat('wavelet/tests/signal_data/channel1/k_get_result.mat')
    expected_ka = kget_state['ka'][0][0]
    input_kmax = kget_state['k_max'][0][0]
    input_N = kget_state['N'][0][0]
    input_A = kget_state['A'][0][0]
    return expected_ka, input_N, input_A, input_kmax


# note that matlab indexes from 1, every pointer should be shifted
@pytest.fixture
def pre_enc_vec():
    pre_state = scio.loadmat('wavelet/tests/signal_data/channel1/pre_enc_vec.mat')
    v = pre_state['v'][0]
    kod = pre_state['kod']
    p = pre_state['p'][0][0] - 1
    ka = pre_state['ka'][0][0]
    kd = pre_state['kd'][0]
    return v, kod, p, ka, kd


@pytest.fixture(scope='function', params=[
    'wavelet/tests/signal_data/channel1/post_enc_vec.mat'
])
def post_enc_vec(request):
    # post_state = scio.loadmat('wavelet/tests/post_enc_vec.mat')
    post_state = scio.loadmat(request.param)

    kod = post_state['kod'].astype('int64')
    p = post_state['p'][0][0] - 1
    return kod, p

# @pytest.fixture(scope='function', params=[
#
# ])
# def test_fixture()

# @pytest.fixture
# def na_params():
#     kget_state = scio.loadmat('wavelet/tests/na_result.mat')
#     expected_ka = kget_state['ka'][0][0]
#     input_kmax = kget_state['k_max'][0][0]
#     input_N = kget_state['N'][0][0]
#     input_A = kget_state['A'][0][0]
#     return expected_ka, input_N, input_A, input_kmax

root_path = pl.Path('wavelet/tests/signal_data/channel4/loop')
pre_files = list(root_path.glob('pre_na_*_results.mat'))
post_files = list(root_path.glob('post_na_*_results.mat'))
na_filepairs = list(zip(pre_files, post_files))

for pre_file, post_file in na_filepairs:
    if pre_file.name.split('_')[2] != post_file.name.split('_')[2]:
        raise RuntimeError("Different files")


@pytest.fixture(scope='function', params=na_filepairs)
def loop_na_params(request):
    pre_file, post_file = request.param

    state = scio.loadmat(str(pre_file))
    input_v1 = state['v'][0][0]
    input_N0 = state['N0'][0][0]
    input_AMAX = state['A_MAX'][0][0]
    input_N = state['N'][0][0]
    input_A = state['A'][0][0]

    state = scio.loadmat(str(post_file))
    expected_N = state['N'][0][0]
    expected_A = state['A'][0][0]

    return input_N, input_A, input_v1, input_N0, input_AMAX, expected_N, expected_A


pre_files = list(root_path.glob('pre_enc_vect_*_results.mat'))
post_files = list(root_path.glob('post_enc_vect_*_results.mat'))
enc_vect_filepairs = list(zip(pre_files, post_files))
# enc_vect_filepairs = [
#     (
#         pl.Path('wavelet/tests/signal_data/channel4/loop/pre_enc_vect_13_results.mat'),
#         pl.Path('wavelet/tests/signal_data/channel4/loop/post_enc_vect_13_results.mat')
#     )
# ]

# for pre_file, post_file in enc_vect_filepairs:
#     if pre_file.name.split('_')[3] != post_file.name.split('_')[3]:
#         raise RuntimeError("Different files")


@pytest.fixture(scope='function', params=enc_vect_filepairs)
def loop_enc_vec_params(request):
    pre_file, post_file = request.param

    print(pre_file.as_posix(), post_file.as_posix())

    pre_state = scio.loadmat(str(pre_file))

    input_v = pre_state['v'][0]
    input_kod = pre_state['kod'].astype('int64')
    input_p = pre_state['p'][0][0] - 1
    input_ka = pre_state['ka'][0][0]
    input_kd = pre_state['kd'][0]

    post_state = scio.loadmat(str(post_file))

    expected_kod = post_state['kod'].astype('int64')
    expected_p = post_state['p'][0][0] - 1

    return input_v, input_kod, input_p, input_ka, input_kd, expected_kod, expected_p
