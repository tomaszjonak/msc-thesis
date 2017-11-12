import pytest
import contextlib
import time

from .. import SynchronizationService as ss


@contextlib.contextmanager
def sync_service_running(client_queue, server_queue, **kwargs):
    service = ss.SynchronizationService(
        client_queue=client_queue,
        server_queue=server_queue,
        **kwargs
    )
    try:
        yield service
    finally:
        server_queue.put('stop')
        client_queue.put('stop')
        service.stop()


@pytest.mark.timeout(0.5)
def test_creation(storage_path, stage_queue, client_queue, server_queue):

    service = ss.SynchronizationService(
        storage_root=storage_path,
        stage_queue=stage_queue,
        client_queue=client_queue,
        server_queue=server_queue
    )

    assert not stage_queue.get_all()

    server_queue.put('stop')
    client_queue.put('stop')
    service.stop()


@pytest.mark.timeout(0.5)
def test_context_creation(storage_path, stage_queue, client_queue, server_queue):
    with sync_service_running(storage_root=storage_path, stage_queue=stage_queue,
                              client_queue=client_queue, server_queue=server_queue,
                              extensions=[]):
        pass
    assert not stage_queue.get_all()


@pytest.mark.timeout(1.0)
def test_simple_case(storage_path, stage_queue, client_queue, server_queue):
    file_names = ['test1.file', 'test2.file', 'test3.file']
    files = [storage_path.joinpath(file_name) for file_name in file_names]
    for file in files:
        file.write_bytes(b'')
        time.sleep(0.001)

    with sync_service_running(storage_root=storage_path, stage_queue=stage_queue,
                              client_queue=client_queue, server_queue=server_queue,
                              extensions=['file']):
        server_queue.put((files[0], []))
        client_queue.put(files[2])
        # Saddly we need to give time for processing
        time.sleep(0.25)

    stage_state = [storage_path.joinpath(relative_path) for relative_path in stage_queue.get_all()]
    assert stage_state == [files[1]]


@pytest.mark.timeout(2)
def test_vectors(storage_path, stage_queue, client_queue, server_queue, sync_vector):
    files = [storage_path.joinpath(file_name) for file_name in sync_vector.files]
    for file in files:
        file.parent.mkdir(exist_ok=True, parents=True)
        file.write_bytes(b'')
        time.sleep(0.001)

    for file_index in sync_vector.staged:
        stage_queue.put(sync_vector.files[file_index])
    staged_state = stage_queue.get_all()

    with sync_service_running(storage_root=storage_path, stage_queue=stage_queue,
                              client_queue=client_queue, server_queue=server_queue,
                              extensions=sync_vector.extensions):
        server_queue.put((files[sync_vector.first], staged_state))
        client_queue.put(files[sync_vector.last])
        time.sleep(0.25)

    expected_queue_state = [storage_path.joinpath(relative_path) for relative_path in staged_state]
    expected_queue_state += [file for file in files[sync_vector.first + 1:sync_vector.last]
                             if file.suffix.strip('.') in sync_vector.extensions]

    tested_queue_state = [storage_path.joinpath(relative_path) for relative_path in stage_queue.get_all()]
    assert expected_queue_state == tested_queue_state
