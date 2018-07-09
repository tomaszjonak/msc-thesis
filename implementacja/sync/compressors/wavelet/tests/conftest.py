import pytest
from scipy import io as scio
import pathlib as pl

from .. import wavelet_commons

params = wavelet_commons.WaveletParams()


@pytest.fixture
def params():
    return wavelet_commons.WaveletParams()


@pytest.fixture(scope='function', params=[
    'wavelet/tests/source_signals/M171006_032845.lvm',
    'wavelet/tests/source_signals/M171006_152139.lvm',
    'wavelet/tests/source_signals/M171006_183622.lvm',
    'wavelet/tests/source_signals/M171006_201801.lvm'
])
def bad_signal_file_encode(request):
    return pl.Path(request.param)


@pytest.fixture(scope='function', params=[
    'wavelet/tests/source_signals/M171006_032845.lvm',
    'wavelet/tests/source_signals/M171006_183622.lvm',
    'wavelet/tests/source_signals/M171006_201801.lvm'
])
def bad_signal_file_decode(request):
    return pl.Path(request.param)


@pytest.fixture(scope='function', params=[
    'wavelet/tests/signal_data/M171006_183622/channel1',
    'wavelet/tests/signal_data/M171006_183622/channel4',
    'wavelet/tests/signal_data/M171006_032845/channel1',
    'wavelet/tests/signal_data/M171006_032845/channel4'
])
def fdwt_matlab_state(request):
    state = scio.loadmat(request.param + '/fdwt_results.mat')
    x = state['x'][0]
    xa = state['xa'][0]
    xd = [elem[0] for elem in state['xd'][0]]
    return x, xa, xd


@pytest.fixture(scope='function', params=[
    'wavelet/tests/signal_data/M171006_183622/channel1',
    'wavelet/tests/signal_data/M171006_183622/channel4',
    'wavelet/tests/signal_data/M171006_032845/channel1',
    'wavelet/tests/signal_data/M171006_032845/channel4'
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
    'wavelet/tests/signal_data/M171006_183622/channel1',
    'wavelet/tests/signal_data/M171006_183622/channel4',
    'wavelet/tests/signal_data/M171006_032845/channel1',
    'wavelet/tests/signal_data/M171006_032845/channel4'
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
    'wavelet/tests/signal_data/M171006_183622/channel4'
])
def kopt_matlab_state(request):
    state = scio.loadmat(request.param + '/kopt_results.mat')

    ka = state['ka'][0][0]
    kd = state['kd'][0]
    xa = state['xa'][0]
    xd = state['xd'][0]

    return ka, kd, xa, xd


@pytest.fixture(scope='function', params=[
    'wavelet/tests/signal_data/M171006_183622/channel4'
])
def kget_matlab_state(request):
    state = scio.loadmat(request.param + '/kget_results.mat')

    expected_ka = state['ka'][0][0]
    input_N = state['N'][0][0]
    input_A = state['A'][0][0]
    input_kmax = state['k_max'][0][0]

    return expected_ka, input_N, input_A, input_kmax


@pytest.fixture(scope='function', params=[
    'wavelet/tests/signal_data/M171006_183622/channel4'
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
    'wavelet/tests/signal_data/M171006_183622/channel4'
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
    'wavelet/tests/signal_data/M171006_183622/channel4'
])
def cw2bs_matlab_state(request):
    state = scio.loadmat(request.param + '/cw2bs_results.mat')

    input_kod = state['kod'].astype('int64')
    expected_bs = state['bs'][0]

    return input_kod, expected_bs


@pytest.fixture(scope='function', params=[
    'wavelet/tests/signal_data/M171006_032845/channel4'
])
def gr0_matlab_state(request):
    state = scio.loadmat(request.param + '/gr0_results.mat')

    v = state['v'][0][0]
    ka = state['ka'][0][0]
    esc_q = state['ESC_Q'][0][0]
    esc_v = state['ESC_V'][0][0]
    expected_cw = state['cw'][0][0]
    expected_cn = state['cn'][0][0]

    return v, ka, esc_q, esc_v, expected_cw, expected_cn


@pytest.fixture(scope='function', params=[
    'wavelet/tests/signal_data/M171006_183622/channel1',
    'wavelet/tests/signal_data/M171006_032845/channel1'
])
def bs_read_matlab_state(request):
    state = scio.loadmat(request.param + '/bs_read_results.mat')

    bs = state['bs'][0]
    N = state['N'][0]
    x = bytearray(el[0] for el in state['x'])

    return x, bs, N


@pytest.fixture(scope='function', params=[
    'wavelet/tests/signal_data/M171006_032845/channel1'
])
def iwt_matlab_state(request):
    state = scio.loadmat(request.param + '/iwt_results.mat')

    original_len = state['original_len'][0][0]
    xa2 = state['xa2'][0]
    xd2 = [elem[0] for elem in state['xd2'][0]]
    expected_x2 = state['x2'][0]

    return original_len, xa2, xd2, expected_x2


@pytest.fixture(scope='function', params=[
    'wavelet/tests/signal_data/M171006_032845/channel1'
])
def decv3_matlab_state(request):
    state = scio.loadmat(request.param + '/decv3_results.mat')

    bytestream = state['bytestream'][0]
    n_levels = state['n_levels'][0][0]
    original_len = state['original_len'][0][0]
    ka = state['ka'][0][0]
    kd = state['kd'][0]
    expected_xa2 = state['xa2'][0]
    expected_xd2 = [elem[0] for elem in state['xd2'][0]]

    return bytestream, n_levels, original_len, ka, kd, expected_xa2, expected_xd2
