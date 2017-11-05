import pytest
import tempfile
import collections
import pathlib as pl

from ...utils import PersistentQueue
from ...utils import StreamProxy
from ...utils import StreamTokenWriter
from ...utils import StreamTokenReader


@pytest.fixture(scope='function')
def stage_queue():
    # TODO, nest this under storage_root
    f = tempfile.NamedTemporaryFile(delete=False)
    cache_instance = PersistentQueue.SqliteQueue(f.name)
    yield cache_instance
    # TODO looks like it leaves file in tmp under windows
    # did no tests on linux, bash on windows makes me lazy
    f.delete = True
    f.close()


@pytest.fixture(scope='function')
def storage_path():
    path = tempfile.TemporaryDirectory()
    yield pl.Path(path.name)
    path.cleanup()


@pytest.fixture(scope='function')
def istream():
    stream = StreamProxy.ByteStream()
    writer = StreamTokenWriter.StreamTokenWriter(stream, '\r\n')
    reader = StreamTokenReader.StreamTokenReader(stream, '\r\n')

    IStream = collections.namedtuple('IStream', ('reader', 'writer'))
    return IStream(reader, writer)


@pytest.fixture(scope='function')
def ostream():
    stream = StreamProxy.ByteStream()
    writer = StreamTokenWriter.StreamTokenWriter(stream, '\r\n')
    reader = StreamTokenReader.StreamTokenReader(stream, '\r\n')

    OStream = collections.namedtuple('OStream', ('reader', 'writer'))
    return OStream(reader, writer)


@pytest.fixture(scope='session')
def extensions():
    return ['avi', 'tmp', 'lvm']


@pytest.fixture(scope='function', params=[
    (
        ('one/file.tmp',    100),
        ('second/file.tmp', 100)
    ),
    (
        ('one/file.tmp',    50),
        ('second/file.tmp', 100)
    ),
    (
        ('one/file.tmp',    100),
        ('second/file.tmp', 50)
    ),
    # W obecnej implementacji wysylanie plikow o dlugosci zero moze sie nie powiesc
    # (
    #     ('one/file.tmp',    0),
    #     ('second/file.tmp', 0)
    # ),
    (
        ('cat/0.tmp', 30),
        ('cat/1.tmp', 30),
        ('cat/2.tmp', 30),
        ('cat/3.tmp', 30),
    ),
    (
        ('cat0/0.tmp', 30),
        ('cat0/1.tmp', 30),
        ('cat1/2.tmp', 30),
        ('cat1/3.tmp', 30),
    ),
    (
        ('cat0/0.tmp', 30),
        ('cat1/1.tmp', 30),
        ('cat2/2.tmp', 30),
        ('cat3/3.tmp', 30),
    ),
    (
        ('file.ext', 1),
        ('file2.ext', 1),
    ),
    ( # files will be discovered in order of extensions passed to processor
        ('file.avi', 1),
        ('file.tmp', 1),
        ('file.lvm', 1)
    ),
    (
        ('file.avi', 1),
        ('file.tmp', 1),
        ('file.lvm', 1),
        ('file.ext', 1),
    ),
    (
        ('file.ext', 1),
        ('file.avi', 1),
        ('file.tmp', 1),
        ('file.lvm', 1),
    ),
    (
        ('file.avi', 1),
        ('file.ext', 1),
        ('file.tmp', 1),
        ('file.lvm', 1),
    ),
])
def file_vector(request):
    return request.param