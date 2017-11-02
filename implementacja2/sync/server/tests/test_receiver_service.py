import pytest
import socket
import time

from .. import DataReceiverService as service
from ...utils import StreamProxy
from ...utils import StreamTokenReader

service_address = '127.0.0.1', 8887


def test_creation(server_root_path, cache):
    tested_service = service.DataReceiverService(service_address, server_root_path.name, cache)
    assert tested_service.is_running()
    tested_service.stop()


def test_get_initial_empty_cache(pan_tadeusz_file, server_root_path, cache):
    tested_service = service.DataReceiverService(service_address, server_root_path.name, cache)
    sock = socket.create_connection(service_address)
    stream = StreamProxy.SocketStreamProxy(sock)
    reader = StreamTokenReader.StreamTokenReader(stream, b'\r\n')
    assert tested_service.is_running()
    assert not reader.get_token()
    tested_service.stop()
