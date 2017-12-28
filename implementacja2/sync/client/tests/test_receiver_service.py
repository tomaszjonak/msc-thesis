import pytest
import pathlib as pl
import time
from contextlib import contextmanager

from .. import ReceiverService as srv
from ...utils import PersistentQueue
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


@pytest.mark.timeout(3)
def test_functional_vectors(service_address, queue_file, storage_path, extensions, file_vector):
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
            time.sleep(2)
            conn.close()

    # It is risky to use same SqliteQueue object in two threads (damn you sqlite3)
    # if needed create 2 objects pointing to same storage file
    queue_view_2 = PersistentQueue.SqliteQueue(queue_file)
    for file in expected_results:
        result = queue_view_2.get()
        assert storage_path.joinpath(result) == file
        queue_view_2.pop(result)


@pytest.mark.skip
def test_synchronization_notification(service_address, queue_file, storage_path, client_queue):
    queue_view1 = PersistentQueue.SqliteQueue(queue_file)

    ext = 'ext'
    stub_path = 'file'
    file = storage_path.joinpath(stub_path)
    file_with_ext = file.with_suffix('.{}'.format(ext))
    file_with_ext.write_bytes(b'')

    with ctx.listener_context(service_address) as s:
        with receiver_service(service_address, queue_view1, storage_path,
                              retry_time=0.5, extensions=[ext],
                              sync_queue=client_queue) as service:
            assert service.is_running()
            conn, _ = s.accept()
            conn.send((stub_path + '\n').encode())
            # TODO change connection to some context type for sanity sake
            conn.close()

    assert client_queue.get() == file_with_ext
    assert client_queue.empty()


@pytest.mark.skip
def test_synchroniaztion_notification(service_address, queue_file, storage_path, client_queue):
    queue_view1 = PersistentQueue.SqliteQueue(queue_file)

    ext = 'ext'
    file_names = ['file1', 'file2', 'file3']
    files = []
    for file_name in file_names:
        file = storage_path.joinpath(file_name).with_suffix('.{}'.format(ext))
        file.write_bytes(b'')
        files.append(file)

    with ctx.listener_context(service_address) as s:
        with receiver_service(service_address, queue_view1, storage_path,
                              retry_time=0.5, extensions=[ext],
                              sync_queue=client_queue) as service:
            assert service.is_running()
            conn, _ = s.accept()
            for file_name in file_names:
                conn.send((file_name + '\n').encode())
            conn.close()

    assert client_queue.get() == files[0]
    assert client_queue.empty()
