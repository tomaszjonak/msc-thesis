import pytest
import contextlib
import os

from .. import SenderService
from ...utils import StreamProxy
from ...utils import StreamTokenReader
from ...utils import StreamTokenWriter
from ...utils import contexts as ctx


@contextlib.contextmanager
def sender_service_running(*args, **kwargs):
    service = SenderService.SenderService(*args, **kwargs, retry_time=0.1)
    try:
        yield service
    finally:
        service.stop()


def test_creation(service_address, storage_path, stage_queue, server_queue):
    service = SenderService.SenderService(
        address=service_address,
        storage_root=storage_path,
        stage_queue=stage_queue,
        sync_queue=server_queue,
        retry_time=0.2
    )
    service.stop()


@pytest.mark.timeout(1)
def test_null_connection_service_first(service_address, storage_path, stage_queue, server_queue):
    with sender_service_running(service_address, storage_path, stage_queue, server_queue):
        with ctx.listener_context(service_address) as listener:
            conn, _ = listener.accept()
            conn.close()


@pytest.mark.timeout(1)
def test_null_connection_listener_first(service_address, storage_path, stage_queue, server_queue):
    with ctx.listener_context(service_address) as listener:
        with sender_service_running(service_address, storage_path, stage_queue, server_queue):
            conn, _ = listener.accept()
            conn.close()


def test_operation_basic(service_address, storage_path, stage_queue, server_queue):
    test_file = 'test/file.tmp'
    file_content = b'correct horse battery staple'
    file_path = storage_path.joinpath(test_file)
    file_path.parent.mkdir(exist_ok=True, parents=True)
    file_path.write_bytes(file_content)
    stage_queue.put('test/file.tmp')
    stage_queue.put('')

    with ctx.listener_context(service_address) as listener:
        with sender_service_running(service_address, storage_path, stage_queue, server_queue) as service:
            assert service.is_alive()
            conn, _ = listener.accept()
            conn.send(b'\r\n')
            stream = StreamProxy.SocketStreamProxy(conn)
            reader = StreamTokenReader.StreamTokenReader(stream, '\r\n')
            assert reader.get_token() == test_file.encode()
            content_len = int(reader.get_token())
            assert reader.get_bytes(content_len) == file_content
            # conn.send((test_file + '\r\n').encode())
            conn.close()


def test_vectors(service_address, storage_path, stage_queue, server_queue, file_vector):
    expected_data = []
    for relative_path, size in file_vector:
        content = os.urandom(size)
        file = storage_path.joinpath(relative_path)
        file.parent.mkdir(exist_ok=True, parents=True)
        file.write_bytes(content)
        stage_queue.put(relative_path)
        expected_data.append((relative_path, size, content))
    ender_file = ''
    stage_queue.put(ender_file)

    with ctx.listener_context(service_address) as listener:
        with sender_service_running(service_address, storage_path, stage_queue, server_queue) as service:
            assert service.is_alive()
            conn, _ = listener.accept()
            conn.send(b'\r\n')
            stream = StreamProxy.SocketStreamProxy(conn)
            reader = StreamTokenReader.StreamTokenReader(stream, '\r\n')
            writer = StreamTokenWriter.StreamTokenWriter(stream, '\r\n')
            for relative_path, size, content in expected_data:
                writer.write_token(relative_path)
                assert reader.get_token() == relative_path.encode()
                assert int(reader.get_token()) == size
                assert reader.get_token() == content
            conn.close()

    stage_state = [relative_path for relative_path, _ in file_vector] + ['']
    assert server_queue.get() == (storage_path.joinpath(''), stage_state)
