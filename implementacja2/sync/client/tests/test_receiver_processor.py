import pytest
import time

from .. import ReceiverProcessor as rp


def test_creation(istream, client_cache, storage_path, stage_queue, extensions):
    processor = rp.ReceiverProcessor(
        reader=istream.reader,
        queue=stage_queue,
        supported_extensions=extensions,
        cache=client_cache,
        storage_root=storage_path
    )

    with pytest.raises(BrokenPipeError):
        processor.run()


# TODO refactor to accept arbitrary order of extensions for single file pattern
def test_vectors(istream, storage_path, client_cache, stage_queue, extensions, file_vector):
    expected_paths = []
    for file_relative_path, _ in file_vector:
        file = storage_path.joinpath(file_relative_path)
        file.parent.mkdir(exist_ok=True, parents=True)
        # we dont really write but create file
        file.write_bytes(b'')
        istream.writer.write_token(file_relative_path.encode())
        if file.suffix.lstrip('.') in extensions:
            expected_paths.append(file)

    processor = rp.ReceiverProcessor(
        reader=istream.reader,
        queue=stage_queue,
        supported_extensions=extensions,
        cache=client_cache,
        storage_root=storage_path
    )

    with pytest.raises(BrokenPipeError):
        processor.run()

    for expected_path in expected_paths:
        path = stage_queue.get()
        # comparing pl.Path objects gets rid of issues with linux/window path conventions
        assert storage_path.joinpath(path) == expected_path
        stage_queue.pop(path)


def test_sync_queue_noop(istream, storage_path, stage_queue, client_queue, client_cache):
    queued_relative_path = 'test_file.ext'
    queued_file = storage_path.joinpath(queued_relative_path)
    queued_file.write_bytes(b'')

    istream.writer.write_token(queued_relative_path)

    processor = rp.ReceiverProcessor(
        reader=istream.reader,
        queue=stage_queue,
        supported_extensions=['ext'],
        storage_root=storage_path,
        sync_queue=client_queue,
        cache=client_cache
    )

    with pytest.raises(BrokenPipeError):
        processor.run()

    assert client_queue.empty


def test_sync_queue_single(istream, storage_path, stage_queue, client_queue, client_cache):
    cached_file_relative_path = 'cached_file.ext'
    cached_file = storage_path.joinpath(cached_file_relative_path)
    cached_file.write_bytes(b'')
    client_cache.put(cached_file_relative_path)

    queued_relative_path = 'test_file.ext'
    queued_file = storage_path.joinpath(queued_relative_path)
    queued_file.write_bytes(b'')

    istream.writer.write_token(queued_relative_path)

    processor = rp.ReceiverProcessor(
        reader=istream.reader,
        queue=stage_queue,
        supported_extensions=['ext'],
        storage_root=storage_path,
        sync_queue=client_queue,
        cache=client_cache
    )

    with pytest.raises(BrokenPipeError):
        processor.run()

    begin_file, end_file, stage_snapshot = client_queue.get()
    assert begin_file == cached_file
    assert end_file == queued_file
    assert not stage_snapshot
    assert client_cache.instant_get() == queued_relative_path


def test_sync_queue_update_multiple_inserts(istream, storage_path, stage_queue, client_queue, client_cache):
    cached_file_relative_path = 'cached_file.ext'
    cached_file = storage_path.joinpath(cached_file_relative_path)
    cached_file.write_bytes(b'')

    client_cache.put(cached_file_relative_path)

    relative_paths = ['f1.ext', 'f2.ext', 'f3.ext', 'f4.ext']
    paths = [storage_path.joinpath(relative_path) for relative_path in relative_paths]
    for path in paths:
        time.sleep(0.01)
        path.write_bytes(b'')
        istream.writer.write_token(str(path.relative_to(storage_path)))

    processor = rp.ReceiverProcessor(
        reader=istream.reader,
        queue=stage_queue,
        supported_extensions=['ext'],
        storage_root=storage_path,
        sync_queue=client_queue,
        cache=client_cache
    )

    with pytest.raises(BrokenPipeError):
        processor.run()

    begin_file, end_file, stage_snapshot = client_queue.get(timeout=1)

    assert begin_file == cached_file
    assert end_file == paths[0]
    assert not stage_snapshot
    assert client_cache.instant_get() == paths[-1].relative_to(storage_path).as_posix()
