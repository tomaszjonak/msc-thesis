import pytest
import tempfile
import pathlib as pl

from .. import FilesystemHelpers as fh
from .. import StreamProxy as sp
from .. import PersistentQueue


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


@pytest.fixture(scope='function')
def queue():
    # TODO, nest this under storage_root
    f = tempfile.NamedTemporaryFile(delete=False)
    cache_instance = PersistentQueue.SqliteQueue(f.name)
    yield cache_instance
    # TODO looks like it leaves file in tmp under windows
    # did no tests on linux, bash on windows makes me lazy
    f.delete = True
    f.close()


@pytest.fixture(scope='function')
def file():
    f = tempfile.NamedTemporaryFile(delete=False)
    yield f.name
    f.delete = True
    f.close()


@pytest.fixture(scope='function')
def directory_path():
    path = tempfile.TemporaryDirectory()
    yield pl.Path(path.name)
    path.cleanup()
