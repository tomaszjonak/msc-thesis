import pytest

from .. import FilesystemHelpers as fh
from .. import StreamProxy as sp


@pytest.fixture(scope='function')
def eof():
    filepath = fh.get_relative_path(__file__, 'vectors/instant_eof.vector')
    stream = sp.FileStreamProxy(filepath)
    return filepath, stream


@pytest.fixture(scope='function')
def one_empty_token():
    filepath = fh.get_relative_path(__file__, 'vectors/one_empty_token.vector')
    stream = sp.FileStreamProxy(filepath)
    return filepath, stream


@pytest.fixture(scope='function')
def two_tokens():
    filepath = fh.get_relative_path(__file__, 'vectors/two_tokens.vector')
    stream = sp.FileStreamProxy(filepath)
    return filepath, stream


@pytest.fixture(scope='function')
def pan_tadeusz_1000_bytes():
    filepath = fh.get_relative_path(__file__, 'vectors/pan_tadzio.vector')
    stream = sp.FileStreamProxy(filepath)
    return filepath, stream

@pytest.fixture(scope='function')
def pan_tadeusz_txt():
    filepath = fh.get_relative_path(__file__, 'vectors/pan-tadeusz-czyli-ostatni-zajazd-na-litwie.txt')
    return filepath