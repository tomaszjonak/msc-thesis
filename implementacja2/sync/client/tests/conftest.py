import pytest
import tempfile
import collections
import pathlib as pl

from ...utils import PersistentQueue
from ...utils import StreamProxy
from ...utils import StreamTokenWriter
from ...utils import StreamTokenReader


# TODO: check whether automatic port discovery could be used here
service_port = 20000


@pytest.fixture(scope='function')
def service_address():
    global service_port
    host = '127.0.0.1'
    address = host, service_port
    service_port += 1
    return address


@pytest.fixture(scope='function')
def queue_file():
    f = tempfile.NamedTemporaryFile(delete=False)
    yield f.name
    # TODO looks like it leaves file in tmp under windows
    # did no tests on linux, bash on windows makes me lazy
    f.delete = True
    f.close()


@pytest.fixture(scope='function')
def stage_queue(queue_file):
    cache_instance = PersistentQueue.SqliteQueue(queue_file)
    yield cache_instance


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

@pytest.fixture(scope='session', params=[
    {
        'files': [  # file order matters here, order introduced by creation time is based on this
            "f1/a.ext",
            "f2/a.ext",
            "f3/a.ext"
        ],
        'first': 0,
        'last': 2,
        'staged': [],
        'extensions': ['ext']
    },
    {
        'files': [  # file order matters here, order introduced by creation time is based on this
            "f1/a.ext",
            "f1/b.ext",
            "f1/c.ext",
            "f2/a.ext",
            "f2/b.ext",
            "f2/c.ext"
        ],
        'first': 2,
        'last': 5,
        'staged': [],
        'extensions': ['ext']
    },
    {
        'files': [  # file order matters here, order introduced by creation time is based on this
            "f1/a.ext",
            "f1/b.ext",
            "f1/c.ext",
            "f2/a.ext",
            "f2/b.ext",
            "f2/c.ext"
        ],
        'first': 1,
        'last': 4,
        'staged': [2, 3],
        'extensions': ['ext']
    },
    {
        'files': [  # file order matters here, order introduced by creation time is based on this
            "f1/a.ext",
            "f1/b.txt",
            "f1/c.xD",
            "f2/a.ext",
            "f2/b.ext",
            "f2/c.ext"
        ],
        'first': 0,
        'last': 5,
        'staged': [4, 3],
        'extensions': ['ext']
    },
    {
        'files': [  # file order matters here, order introduced by creation time is based on this
            "f1/a.lvm",
            "f1/a.avi",
            "f1/a.ext",
            "f2/a.lvm",
            "f2/a.avi",
            "f2/a.ext"
        ],
        'first': 0,
        'last': 5,
        'staged': [],
        'extensions': ['lvm,avi,ext']
    },
    {
        'files': [  # file order matters here, order introduced by creation time is based on this
            "f1/a.lvm",
            "f1/a.avi",
            "f1/a.ext",
            "f2/a.lvm",
            "f2/a.avi",
            "f2/a.ext"
        ],
        'first': 0,
        'last': 5,
        'staged': [1, 3, 5],
        'extensions': ['lvm,avi,ext']
    },
])
def sync_vector(request):
    dct = request.param
    SyncState = collections.namedtuple('SyncState', ('files', 'first', 'last', 'staged', 'extensions'))

    vector = SyncState(
        files=dct['files'],
        first=dct['first'],
        last=dct['last'],
        staged=dct['staged'],
        extensions=dct['extensions']
    )

    return vector
