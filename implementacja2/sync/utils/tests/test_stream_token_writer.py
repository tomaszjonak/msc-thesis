import pytest
import tempfile

from .. import StreamTokenWriter as stw
from .. import StreamProxy as sp


@pytest.fixture(scope='function')
def stream_writer():
    def make_writer(stream):
        return stw.StreamTokenWriter(stream, '\r\n')
    return make_writer


@pytest.fixture(scope='function')
def tmp_data():
    # note: tmpfile closes itself when it goes out of scope
    tmp_file = tempfile.NamedTemporaryFile()
    temp_stream = sp.TempFileStreamProxy(tmp_file, tmp_file)
    writer = stw.StreamTokenWriter(temp_stream, '\r\n')
    return tmp_file, writer


def test_noop(tmp_data):
    tmp_fd, tmp_writer = tmp_data

    assert tmp_fd.read() == bytes()


def test_empty_token_write(tmp_data, one_empty_token):
    expected_path, _ = one_empty_token
    temp_fd, temp_writer = tmp_data

    temp_writer.write_token('')

    with open(expected_path, 'rb') as expected_fd:
        # saddly seek here is needed as temp_writer calls write on temp_fd internally
        temp_fd.seek(0)
        assert temp_fd.read() == expected_fd.read()


def test_two_tokens(tmp_data, two_tokens):
    expected_path, _ = two_tokens
    temp_fd, temp_writer = tmp_data
    temp_writer.write_token('first_line')
    temp_writer.write_token('second_line')

    with open(expected_path, 'rb') as expected_fd:
        temp_fd.seek(0)
        assert temp_fd.read() == expected_fd.read()


def test_pan_tadeusz_1000_bytes(tmp_data, pan_tadeusz_1000_bytes, pan_tadeusz_txt):
    expected_path, _ = pan_tadeusz_1000_bytes
    temp_fd, temp_writer = tmp_data
    pan_tadeusz_name = 'pan-tadeusz-czyli-ostatni-zajazd-na-litwie.txt'


    temp_writer.write_token(pan_tadeusz_name)
    temp_writer.write_token('1000')
    with open(pan_tadeusz_txt, 'rb') as fd:
        temp_writer.write_bytes(fd.read(1000))
    temp_writer.write_separator()

    temp_fd.seek(0)
    with open(expected_path, 'rb') as expected_fd:
        assert temp_fd.read() == expected_fd.read()