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


def test_creation(service_address, server_root_path):
    tested_service = service.DataReceiverService(service_address, server_root_path.name)
    assert tested_service.is_running()
    tested_service.stop()


def get_valid_path(path):
    return pl.Path(fsh.get_relative_path(__file__, path))


def test_file_inputs(service_address, server_root_path, vector_description):
    storage_root = server_root_path.name
    with receiver_service_running(service_address, server_root_path.name) as srv:
        assert srv.is_running()
        with cmgr.connection_context(service_address) as ctx:
            vector_file = get_valid_path(vector_description.vector_path)
            ctx.connection.sendall(vector_file.read_bytes())
            assert all(ctx.reader.get_token() == token.encode() for token in vector_description.ack_sequence)

    for file_group in vector_description.file_groups:
        source_path = get_valid_path(file_group.source_path)
        source_bytes = source_path.read_bytes()
        for file_desc in file_group.file_states:
            file_path = pl.Path(storage_root, file_desc.path)
            assert file_path.read_bytes() == source_bytes[:file_desc.size]
