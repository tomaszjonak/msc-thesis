import pytest

from .. import ReceiverProcessor as rp


def test_creation(istream, storage_path, stage_queue, extensions):
    processor = rp.ReceiverProcessor(
        reader=istream.reader,
        queue=stage_queue,
        supported_extensions=extensions,
        storage_root=storage_path
    )

    with pytest.raises(RuntimeError):
        processor.run()


# TODO refactor to accept arbitral order of extensions for single file pattern
def test_vectors(istream, storage_path, stage_queue, extensions, file_vector):
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
        storage_root=storage_path
    )

    with pytest.raises(RuntimeError):
        processor.run()

    for expected_path in expected_paths:
        path = stage_queue.get()
        # comparing pl.Path objects gets rid of issues with linux/window path conventions
        assert storage_path.joinpath(path) == expected_path
        stage_queue.pop(path)


def test_sync_queue_update(istream, storage_path, stage_queue, client_queue):
    relative_path = 'test_file.ext'
    first_file = storage_path.joinpath(relative_path)
    first_file.write_bytes(b'')

    istream.writer.write_token(relative_path)

    processor = rp.ReceiverProcessor(
        reader=istream.reader,
        queue=stage_queue,
        supported_extensions=['ext'],
        storage_root=storage_path,
        sync_queue=client_queue
    )

    with pytest.raises(RuntimeError):
        processor.run()

    returned_file = client_queue.get(timeout=1)
    assert returned_file == first_file
    assert client_queue.empty()


def test_sync_queue_update_multiple_inserts(istream, storage_path, stage_queue, client_queue):
    relative_paths = ['f1.ext', 'f2.ext', 'f3.ext', 'f4.ext']
    paths = [storage_path.joinpath(relative_path) for relative_path in relative_paths]
    for path in paths:
        path.write_bytes(b'')
        istream.writer.write_token(str(path.relative_to(storage_path)))

    processor = rp.ReceiverProcessor(
        reader=istream.reader,
        queue=stage_queue,
        supported_extensions=['ext'],
        storage_root=storage_path,
        sync_queue=client_queue
    )

    with pytest.raises(RuntimeError):
        processor.run()

    returned_file = client_queue.get(timeout=1)
    assert returned_file == paths[0]
    assert client_queue.empty()


def test_sync_queue_update_multiple_invalid(istream, storage_path, stage_queue, client_queue):
    relative_paths = ['f1.ext', 'f2.ext', 'f3.ext', 'f4.ext']
    paths = [storage_path.joinpath(relative_path) for relative_path in relative_paths]
    for path in paths:
        path.write_bytes(b'')
        istream.writer.write_token(str(path.relative_to(storage_path)))

    processor = rp.ReceiverProcessor(
        reader=istream.reader,
        queue=stage_queue,
        supported_extensions=[],
        storage_root=storage_path,
        sync_queue=client_queue
    )

    with pytest.raises(RuntimeError):
        processor.run()

    assert client_queue.empty()
