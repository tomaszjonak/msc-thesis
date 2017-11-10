import pytest
import pathlib as pl
from contextlib import contextmanager

from .. import ReceiverService as srv
from ...utils import contexts as ctx


@contextmanager
def receiver_service(*args, **kwargs):
    service_ = srv.ReceiverService(*args, **kwargs)
    try:
        yield service_
    finally:
        service_.stop()


def test_creation(service_address, stage_queue, storage_path):
    service_ = srv.ReceiverService(service_address, stage_queue, storage_path, retry_time=0.5)
    service_.stop()


# TODO those tests are dedicated to KeepAliveWorker, move to utils
@pytest.mark.timeout(2)  # timeout is in seconds
def test_connection_service_exists(service_address, stage_queue, storage_path):
    with ctx.listener_context(service_address) as s:
        with receiver_service(service_address, stage_queue, storage_path, retry_time=0.5):
            conn, _ = s.accept()
            conn.close()


@pytest.mark.timeout(2)
def test_connection_service_starts(service_address, stage_queue, storage_path):
    with receiver_service(service_address, stage_queue, storage_path, retry_time=0.5):
        with ctx.listener_context(service_address) as s:
            conn, _ = s.accept()
            conn.close()


@pytest.mark.timeout(2)
def test_functional_one_element(service_address, stage_queue, storage_path):
    fname = 'top/kek'
    file = storage_path.joinpath(fname).with_suffix('.avi')  # extension from service defaults
    file.parent.mkdir(parents=True)
    file.write_bytes(b'')  # file creation

    with ctx.listener_context(service_address) as s:
        with receiver_service(service_address, stage_queue, storage_path, retry_time=0.5) as service:
            assert service.is_running()
            conn, _ = s.accept()
            conn.send((fname + '\n').encode())
            conn.close()

    assert storage_path.joinpath(stage_queue.get()) == file


def test_functional_vectors(service_address, queue_file, storage_path, extensions, file_vector):
    from ...utils import PersistentQueue
    queue_view_1 = PersistentQueue.SqliteQueue(queue_file)

    expected_results = []
    for relative_path, _ in file_vector:
        file = storage_path.joinpath(relative_path)
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(b'')

        if file.suffix.strip('.') in extensions:
            expected_results.append(file)

    with ctx.listener_context(service_address) as s:
        with receiver_service(service_address, queue_view_1, storage_path,
                              retry_time=0.5, extensions=extensions) as service:
            assert service.is_running()
            conn, _ = s.accept()
            for relative_path, _ in file_vector:
                path_without_extension = str(pl.Path(relative_path).with_suffix(''))
                conn.send((path_without_extension + '\n').encode())
            conn.close()

    # It is risky to use same SqliteQueue object in two threads (damn you sqlite3)
    # if needed create 2 objects pointing to same storage file (
    queue_view_2 = PersistentQueue.SqliteQueue(queue_file)
    for file in expected_results:
        result = queue_view_2.get()
        assert storage_path.joinpath(result) == file
        queue_view_2.pop(result)
