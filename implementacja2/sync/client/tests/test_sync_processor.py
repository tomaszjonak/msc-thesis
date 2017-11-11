import pytest

from .. import SyncProcessor
from ...utils import PersistentQueue


def test_creation(queue_file, extensions, storage_path):
    queue = PersistentQueue.SqliteQueue(queue_file)
    processor = SyncProcessor.SyncProcessor(
        queue_view=queue,
        extensions=extensions,
        storage_root=storage_path,
        staged_files=[],
    )

    assert not queue.get_all()


def test_basic_run(queue_file, storage_path):
    queue = PersistentQueue.SqliteQueue(queue_file)

    file1 = storage_path.joinpath('file1.ext')
    file1.write_bytes(b'')
    file2 = storage_path.joinpath('file2.ext')
    file2.write_bytes(b'')
    file3 = storage_path.joinpath('file3.ext')
    file3.write_bytes(b'')

    SyncProcessor.SyncProcessor(
        queue_view=queue,
        extensions=['ext'],
        storage_root=storage_path,
        staged_files=[]
    ).update_queue(file1, file3)

    staged_files = queue.get_all()
    assert 'file2.ext' in staged_files


def test_empty_run(queue_file, storage_path):
    queue = PersistentQueue.SqliteQueue(queue_file)

    file1 = storage_path.joinpath('file1.ext')
    file1.write_bytes(b'')
    file2 = storage_path.joinpath('file2.ext')
    file2.write_bytes(b'')

    SyncProcessor.SyncProcessor(
        queue_view=queue,
        extensions=['ext'],
        storage_root=storage_path,
        staged_files=[]
    ).update_queue(file1, file2)

    staged_files = queue.get_all()
    assert not staged_files


def test_vectorized(queue_file, storage_path, sync_vector):
    queue = PersistentQueue.SqliteQueue(queue_file)

    files = [storage_path.joinpath(file) for file in sync_vector.files]
    for file in files:
        file.parent.mkdir(exist_ok=True, parents=True)
        file.write_bytes(b'')

    [queue.put(sync_vector.files[file_index]) for file_index in sync_vector.staged]

    SyncProcessor.SyncProcessor(
        queue_view=queue,
        extensions=sync_vector.extensions,
        storage_root=storage_path,
        staged_files=[]
    ).update_queue(files[sync_vector.first], files[sync_vector.last])

    staged_expected_files = [files[file_index] for file_index in sync_vector.staged]
    staged_expected_files += [file for file in files[sync_vector.first + 1:sync_vector.last]
                              if file.suffix.strip('.') in sync_vector.extensions]

    staged_current_files = [storage_path.joinpath(file) for file in queue.get_all()]
    assert staged_expected_files == staged_current_files
