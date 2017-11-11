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
