import pytest

from .. import StreamTokenReader as sr
from .. import FilesystemHelpers as fh


@pytest.fixture(scope='function')
def token_reader():
    def make_reader(stream):
        return sr.StreamTokenReader(stream, '\r\n'.encode('utf8'), 8192)
    return make_reader


def test_eof(token_reader, eof):
    _, stream = eof
    reader = token_reader(stream)
    with pytest.raises(RuntimeError):
        reader.get_token()


def test_one_empty_token(token_reader, one_empty_token):
    _, stream = one_empty_token
    reader = token_reader(stream)
    assert '' == reader.get_token().decode('utf8')


def test_two_tokens(token_reader, two_tokens):
    _, stream = two_tokens
    reader = token_reader(stream)
    assert 'first_line' == reader.get_token().decode('utf8')


def test_pan_tadeusz_1000_bytes(token_reader, pan_tadeusz_1000_bytes, pan_tadeusz_txt):
    _, stream = pan_tadeusz_1000_bytes
    reader = token_reader(stream)
    pan_tadeusz_name = 'pan-tadeusz-czyli-ostatni-zajazd-na-litwie.txt'

    assert pan_tadeusz_name == reader.get_token().decode('utf8')
    assert '1000' == reader.get_token().decode('utf8')

    with open(pan_tadeusz_txt, 'rb') as fd:
        assert fd.read(1000) == reader.get_bytes(1000)

    assert '' == reader.get_token().decode('utf8')

    with pytest.raises(RuntimeError):
        reader.get_token()
