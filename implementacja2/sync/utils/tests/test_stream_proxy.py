import pytest
import os

from .. import StreamProxy as sp
from .. import StreamTokenReader as sr


def get_relative_path(name):
    # Returns path relative to this file direcotry
    return os.path.join(os.path.dirname(__file__), name)


@pytest.fixture(scope='function')
def eof():
    return sp.FileStreamProxy(get_relative_path('vectors/instant_eof.vector'))


@pytest.fixture(scope='function')
def one_empty_token():
    return sp.FileStreamProxy(get_relative_path('vectors/one_empty_token.vector'))


@pytest.fixture(scope='function')
def two_tokens():
    return sp.FileStreamProxy(get_relative_path('vectors/two_tokens.vector'))


@pytest.fixture(scope='function')
def pan_tadeusz_1000_bytes():
    return sp.FileStreamProxy(get_relative_path('vectors/pan_tadzio.vector'))


@pytest.fixture(scope='function')
def token_reader():
    def make_reader(stream):
        return sr.StreamTokenReader(stream, '\r\n'.encode('utf8'), 8192)
    return make_reader


def test_eof(token_reader, eof):
    reader = token_reader(eof)
    with pytest.raises(RuntimeError):
        reader.get_token()


def test_one_empty_token(token_reader, one_empty_token):
    reader = token_reader(one_empty_token)
    assert '' == reader.get_token().decode('utf8')


def test_two_tokens(token_reader, two_tokens):
    reader = token_reader(two_tokens)
    assert 'first_line' == reader.get_token().decode('utf8')


def test_pan_tadeusz_1000_bytes(token_reader, pan_tadeusz_1000_bytes):
    reader = token_reader(pan_tadeusz_1000_bytes)
    pan_tadeusz_name = 'pan-tadeusz-czyli-ostatni-zajazd-na-litwie.txt'
    assert pan_tadeusz_name == reader.get_token().decode('utf8')
    assert '1000' == reader.get_token().decode('utf8')
    with open(get_relative_path('vectors/{}'.format(pan_tadeusz_name)), 'rb') as fd:
        assert fd.read(1000) == reader.get_bytes(1000)
    assert '' == reader.get_token().decode('utf8')
    with pytest.raises(RuntimeError):
        reader.get_token()
