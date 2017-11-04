from contextlib import contextmanager
import socket
import collections

from . import StreamProxy
from . import StreamTokenReader
from . import StreamTokenWriter


@contextmanager
def connection(*args, **kwargs):
    conn = socket.create_connection(*args, **kwargs)
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def connection_context(*args, **kwargs):
    with connection(*args, **kwargs) as socket_:
        stream = StreamProxy.SocketStreamProxy(socket_)
        reader = StreamTokenReader.StreamTokenReader(stream, b'\r\n')
        writer = StreamTokenWriter.StreamTokenWriter(stream, b'\r\n')

        ConnectionContext = collections.namedtuple('ConnectionContext', ('connection', 'reader', 'writer'))
        yield ConnectionContext(socket_, reader, writer)
