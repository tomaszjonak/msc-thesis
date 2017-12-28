import pytest
import pathlib as pl
from contextlib import contextmanager

from .. import DataReceiverService as service
from ...utils import FilesystemHelpers as fsh
from ...utils import contexts as cmgr


@contextmanager
def receiver_service_running(*args, **kwargs):
    service_ = service.DataReceiverService(*args, **kwargs)
    try:
        yield service_
    finally:
        service_.stop()


# TODO: check whether automatic port discovery could be used here
service_port = 10000


@pytest.fixture(scope='function')
def service_address():
    global service_port
    host = '127.0.0.1'
    address = host, service_port
    service_port += 1
    return address


def test_creation(service_address, server_root_path, cache):
    tested_service = service.DataReceiverService(service_address, server_root_path.name, cache)
    assert tested_service.is_running()
    tested_service.stop()


def test_get_initial_empty_cache(service_address, server_root_path, cache):
    with receiver_service_running(service_address, server_root_path.name, cache) as srv:
        assert srv.is_running()
        with cmgr.connection_context(service_address) as context:
            token = context.reader.get_token()
            assert not token
        # note that connection has to be closed before service
        # socketserver waits for all connections before finishing shutdown() call


def test_get_initial_set_cache(service_address, server_root_path, cache):
    test_path = 'test/file/path'
    cache.put(test_path)
    with receiver_service_running(service_address, server_root_path.name, cache) as srv:
        assert srv.is_running()
        with cmgr.connection_context(service_address) as context:
            assert test_path == context.reader.get_token().decode()


def get_valid_path(path):
    return pl.Path(fsh.get_relative_path(__file__, path))


def test_file_inputs(service_address, server_root_path, cache, vector_description):
    if vector_description.cache_initial:
        cache.put(vector_description.cache_initial)

    storage_root = server_root_path.name
    with receiver_service_running(service_address, server_root_path.name, cache) as srv:
        assert srv.is_running()
        with cmgr.connection_context(service_address) as ctx:
            vector_file = get_valid_path(vector_description.vector_path)
            ctx.connection.sendall(vector_file.read_bytes())
            assert ctx.reader.get_token().decode() == (vector_description.cache_initial or '')
            assert all(ctx.reader.get_token() == token.encode() for token in vector_description.ack_sequence)

    for file_group in vector_description.file_groups:
        source_path = get_valid_path(file_group.source_path)
        source_bytes = source_path.read_bytes()
        for file_desc in file_group.file_states:
            file_path = pl.Path(storage_root, file_desc.path)
            assert file_path.read_bytes() == source_bytes[:file_desc.size]

    assert cache.get(wait_for_value=False) == vector_description.cache_expected
