import pytest
import tempfile
import pathlib as pl

from ...utils import StreamProxy
from ...utils import StreamTokenReader, StreamTokenWriter
from ...utils import FilesystemHelpers as fsh
from ...utils import PersistentQueue


@pytest.fixture(scope='function')
def cache():
    f = tempfile.NamedTemporaryFile(delete=False)
    cache_instance = PersistentQueue.SqliteQueue(f.name)
    return cache_instance


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
