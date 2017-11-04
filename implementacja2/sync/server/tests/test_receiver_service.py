import pytest
import socket

from .. import DataReceiverService as service
from ...utils import StreamProxy
from ...utils import StreamTokenReader

from contextlib import contextmanager


@contextmanager
def connection(*args, **kwargs):
    conn = socket.create_connection(*args, **kwargs)
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def receiver_service_running(*args, **kwargs):
    service_ = service.DataReceiverService(*args, **kwargs)
    try:
        yield service_
    finally:
        service_.stop()


# TODO: check whether automatic port discovery could be used here
service_address = 10000


@pytest.fixture(scope='function')
def server_address():
    global service_address
    host = '127.0.0.1'
    address = host, service_address
    service_address += 1
    return address


def test_creation(server_address, server_root_path, cache):
    tested_service = service.DataReceiverService(server_address, server_root_path.name, cache)
    assert tested_service.is_running()
    tested_service.stop()


def test_get_initial_empty_cache(server_address, server_root_path, cache):
    with receiver_service_running(server_address, server_root_path.name, cache) as srv:
        assert srv.is_running()
        with connection(server_address) as conn:
            stream = StreamProxy.SocketStreamProxy(conn)
            reader = StreamTokenReader.StreamTokenReader(stream, b'\r\n')
            token = reader.get_token()
            print('token [{}]'.format(repr(token)))
            assert not token
        # note that connection has to be closed before service
        # socketserver waits for all connections before finishing shutdown() call


# def test_get_initil_set_cache(server_address, server_root_path, cache):
