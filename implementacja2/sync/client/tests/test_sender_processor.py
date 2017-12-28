import pytest
import os

from .. import SenderProtocolProcessor as spp


def test_creation(istream, ostream, stage_queue, storage_path):
    processor = spp.SenderProtocolProcessor(
        reader=istream.reader,
        writer=ostream.writer,
        stage_queue=stage_queue,
        storage_root=storage_path
    )

    processor.stop()
    processor.run()


def test_operation_normal(istream, ostream, storage_path, stage_queue, server_queue):
    test_file = 'test/file.tmp'
    file_content = b'correct horse battery staple'
    file_path = storage_path.joinpath(test_file)
    file_path.parent.mkdir(exist_ok=True, parents=True)
    file_path.write_bytes(file_content)
    stage_queue.put('test/file.tmp')
    stage_queue.put('')

    istream.writer.write_separator()

    processor = spp.SenderProtocolProcessor(
        reader=istream.reader,
        writer=ostream.writer,
        stage_queue=stage_queue,
        storage_root=storage_path,
        sync_queue=server_queue
    )

    with pytest.raises(RuntimeError):
        processor.run()

    assert ostream.reader.get_token() == test_file.encode()
    assert ostream.reader.get_token() == str(len(file_content)).encode()
    assert ostream.reader.get_bytes(len(file_content)) == file_content


@pytest.mark.skip
def test_file_vectors(istream, ostream, stage_queue, storage_path, server_queue, file_vector):
    # No cached value from server
    istream.writer.write_separator()

    expected_sequence = []
    for file_path, size in file_vector:
        content = os.urandom(size)
        file = storage_path.joinpath(file_path)
        file.parent.mkdir(exist_ok=True, parents=True)
        file.write_bytes(content)
        # Queue to fetch from
        stage_queue.put(file_path)
        # Server acknowledge
        istream.writer.write_token(file_path)
        expected_sequence.append((file_path.encode(), str(size).encode(), content))
    # TODO changing protocol to enable gracefull test shutdown may be time consuming, investigate
    ender_filename = 'xD'
    storage_path.joinpath(ender_filename).write_bytes(b'')
    stage_queue.put(ender_filename)

    processor = spp.SenderProtocolProcessor(
        reader=istream.reader,
        writer=ostream.writer,
        stage_queue=stage_queue,
        storage_root=storage_path,
        sync_queue=server_queue
    )

    with pytest.raises(RuntimeError):
        processor.run()

    for encoded_file_path, encoded_size, content in expected_sequence:
        assert ostream.reader.get_token() == encoded_file_path
        assert ostream.reader.get_token() == encoded_size
        assert ostream.reader.get_bytes(int(encoded_size.decode())) == content
        assert ostream.reader.get_token() == b''


def test_sync_basic(istream, ostream, stage_queue, storage_path, server_queue):
    expected_file = 'test.file'
    istream.writer.write_token(expected_file)

    ender_filename = 'xD'
    storage_path.joinpath(ender_filename).write_bytes(b'')
    stage_queue.put(ender_filename)

    processor = spp.SenderProtocolProcessor(
        reader=istream.reader,
        writer=ostream.writer,
        stage_queue=stage_queue,
        storage_root=storage_path,
        sync_queue=server_queue
    )

    with pytest.raises(RuntimeError):
        processor.run()

    assert server_queue.get(timeout=2) == (storage_path.joinpath(expected_file), [ender_filename])
