import pytest
import tempfile
import os
import pathlib as pl

from ...utils import StreamProxy
from ...utils import StreamTokenReader, StreamTokenWriter
from ...utils import FilesystemHelpers as fsh
from ...utils import PersistentQueue
from .. import ServerProtocolProcessor


@pytest.fixture(scope='function')
def server_root_path():
    path = tempfile.TemporaryDirectory()
    return path


@pytest.fixture(scope='module')
def pan_tadeusz_file():
    pan_tadeusz_path = fsh.get_relative_path(__file__, 'vectors/pan-tadeusz-czyli-ostatni-zajazd-na-litwie.txt')
    return pl.Path(pan_tadeusz_path)


def prepare_reader(relative_path):
    path = fsh.get_relative_path(__file__, relative_path)
    stream = StreamProxy.FileStreamProxy(path)
    return StreamTokenReader.StreamTokenReader(stream, '\r\n')


@pytest.fixture(scope='function')
def reader_one_file():
    return prepare_reader('vectors/one_file.vector')


@pytest.fixture(scope='function')
def reader_two_equall():
    return prepare_reader('vectors/two_equall_length.vector')


@pytest.fixture(scope='function')
def reader_two_increasing():
    return prepare_reader('vectors/two_increasing_length.vector')


@pytest.fixture(scope='function')
def reader_two_decreasing():
    return prepare_reader('vectors/two_decreasing_length.vector')


@pytest.fixture(scope='function')
def reader_two_no_cache_update():
    return prepare_reader('vectors/two_no_cache_update.vector')


@pytest.fixture(scope='function')
def mock_outstream():
    file = tempfile.NamedTemporaryFile()
    stream = StreamProxy.TempFileStreamProxy(file, file)
    writer = StreamTokenWriter.StreamTokenWriter(stream, '\r\n')

    return file, writer


@pytest.fixture(scope='function')
def cache():
    f = tempfile.NamedTemporaryFile(delete=False)
    cache_instance = PersistentQueue.SqliteQueue(f.name)

    return cache_instance


def test_one_file(server_root_path, cache, reader_one_file, mock_outstream, pan_tadeusz_file):
    file, out_writer = mock_outstream
    processor = ServerProtocolProcessor.ServerProtocolProcessor(reader_one_file, out_writer,
                                                                cache, server_root_path.name)

    with pytest.raises(RuntimeError):
        processor.run()

    assert 'M000101' in os.listdir(server_root_path.name)

    file.seek(0)
    assert file.read() == b'\r\nM000101/M000101-000000\r\n'
    assert cache.get(wait_for_value=False) == 'M000101/M000101-000000'

    generated_file = pl.Path(server_root_path.name, 'M000101/M000101-000000')
    with pan_tadeusz_file.open('rb') as pan_tadeusz:
        assert generated_file.read_bytes() == pan_tadeusz.read(1000)


def test_two_equall_length(server_root_path, cache, reader_two_equall, mock_outstream, pan_tadeusz_file):
    file, out_writer = mock_outstream

    processor = ServerProtocolProcessor.ServerProtocolProcessor(reader_two_equall, out_writer,
                                                                cache, server_root_path.name)

    with pytest.raises(RuntimeError):
        processor.run()

    assert 'M000102' in os.listdir(server_root_path.name)

    file.seek(0)
    assert file.read() == b'\r\nM000102/M000102-000000\r\nM000102/M000102-000001\r\n'
    assert cache.get(wait_for_value=False) == 'M000102/M000102-000001'

    first_file = pl.Path(server_root_path.name, 'M000102/M000102-000000')
    second_file = pl.Path(server_root_path.name, 'M000102/M000102-000001')
    with pan_tadeusz_file.open('rb') as pan_tadeusz:
        pan_tadeusz_1000_bytes = pan_tadeusz.read(1000)
    assert first_file.read_bytes() == pan_tadeusz_1000_bytes
    assert second_file.read_bytes() == pan_tadeusz_1000_bytes


def test_two_increasing_length(server_root_path, cache, reader_two_increasing, mock_outstream, pan_tadeusz_file):
    file, out_writer = mock_outstream

    processor = ServerProtocolProcessor.ServerProtocolProcessor(reader_two_increasing, out_writer,
                                                                cache, server_root_path.name)

    with pytest.raises(RuntimeError):
        processor.run()

    assert 'M000103' in os.listdir(server_root_path.name)

    file.seek(0)
    assert file.read() == b'\r\nM000103/M000103-000000\r\nM000103/M000103-000001\r\n'
    assert cache.get(wait_for_value=False) == 'M000103/M000103-000001'

    first_file = pl.Path(server_root_path.name, 'M000103/M000103-000000')
    second_file = pl.Path(server_root_path.name, 'M000103/M000103-000001')
    with pan_tadeusz_file.open('rb') as pan_tadeusz:
        pan_tadeusz_2000_bytes = pan_tadeusz.read(2000)
    assert first_file.read_bytes() == pan_tadeusz_2000_bytes[:1000]
    assert second_file.read_bytes() == pan_tadeusz_2000_bytes


def test_two_decreasing_length(server_root_path, cache, reader_two_decreasing, mock_outstream, pan_tadeusz_file):
    file, out_writer = mock_outstream

    processor = ServerProtocolProcessor.ServerProtocolProcessor(reader_two_decreasing, out_writer,
                                                                cache, server_root_path.name)

    with pytest.raises(RuntimeError):
        processor.run()

    assert 'M000104' in os.listdir(server_root_path.name)

    file.seek(0)
    assert file.read() == b'\r\nM000104/M000104-000000\r\nM000104/M000104-000001\r\n'
    assert cache.get(wait_for_value=False) == 'M000104/M000104-000001'

    first_file = pl.Path(server_root_path.name, 'M000104/M000104-000000')
    second_file = pl.Path(server_root_path.name, 'M000104/M000104-000001')
    with pan_tadeusz_file.open('rb') as pan_tadeusz:
        pan_tadeusz_2000_bytes = pan_tadeusz.read(2000)
    assert first_file.read_bytes() == pan_tadeusz_2000_bytes
    assert second_file.read_bytes() == pan_tadeusz_2000_bytes[:1000]


def test_no_cache_update(server_root_path, cache, reader_two_no_cache_update, mock_outstream, pan_tadeusz_file):
    file, out_writer = mock_outstream

    processor = ServerProtocolProcessor.ServerProtocolProcessor(reader_two_no_cache_update, out_writer,
                                                                cache, server_root_path.name)

    with pytest.raises(RuntimeError):
        processor.run()

    assert 'M000105' in os.listdir(server_root_path.name)

    file.seek(0)
    assert file.read() == b'\r\nM000105/M000105-000001\r\nM000105/M000105-000000\r\n'
    assert cache.get(wait_for_value=False) == 'M000105/M000105-000001'

    first_file = pl.Path(server_root_path.name, 'M000105/M000105-000000')
    second_file = pl.Path(server_root_path.name, 'M000105/M000105-000001')
    with pan_tadeusz_file.open('rb') as pan_tadeusz:
        pan_tadeusz_100_bytes = pan_tadeusz.read(100)
    assert first_file.read_bytes() == pan_tadeusz_100_bytes
    assert second_file.read_bytes() == pan_tadeusz_100_bytes
