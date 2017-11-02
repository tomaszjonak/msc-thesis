import pytest
import os
import pathlib as pl

from .. import ServerProtocolProcessor


def test_one_file(server_root_path, cache, reader_one_file, mock_outstream, pan_tadeusz_file):
    file, out_writer = mock_outstream
    processor = ServerProtocolProcessor.ServerProtocolProcessor(reader_one_file, out_writer,
                                                                cache, server_root_path.name)

    with pytest.raises(RuntimeError):
        processor.run()

    assert 'M000101' in os.listdir(server_root_path.name)

    file.seek(0)
    assert file.read() == b'\r\nM000101/M000101-000000\r\n'
    assert cache.get(wait_for_value=False) == 'M000101/M000101-000000'

    generated_file = pl.Path(server_root_path.name, 'M000101/M000101-000000')
    with pan_tadeusz_file.open('rb') as pan_tadeusz:
        assert generated_file.read_bytes() == pan_tadeusz.read(1000)


def test_two_equall_length(server_root_path, cache, reader_two_equall, mock_outstream, pan_tadeusz_file):
    file, out_writer = mock_outstream

    processor = ServerProtocolProcessor.ServerProtocolProcessor(reader_two_equall, out_writer,
                                                                cache, server_root_path.name)

    with pytest.raises(RuntimeError):
        processor.run()

    assert 'M000102' in os.listdir(server_root_path.name)

    file.seek(0)
    assert file.read() == b'\r\nM000102/M000102-000000\r\nM000102/M000102-000001\r\n'
    assert cache.get(wait_for_value=False) == 'M000102/M000102-000001'

    first_file = pl.Path(server_root_path.name, 'M000102/M000102-000000')
    second_file = pl.Path(server_root_path.name, 'M000102/M000102-000001')
    with pan_tadeusz_file.open('rb') as pan_tadeusz:
        pan_tadeusz_1000_bytes = pan_tadeusz.read(1000)
    assert first_file.read_bytes() == pan_tadeusz_1000_bytes
    assert second_file.read_bytes() == pan_tadeusz_1000_bytes


def test_two_increasing_length(server_root_path, cache, reader_two_increasing, mock_outstream, pan_tadeusz_file):
    file, out_writer = mock_outstream

    processor = ServerProtocolProcessor.ServerProtocolProcessor(reader_two_increasing, out_writer,
                                                                cache, server_root_path.name)

    with pytest.raises(RuntimeError):
        processor.run()

    assert 'M000103' in os.listdir(server_root_path.name)

    file.seek(0)
    assert file.read() == b'\r\nM000103/M000103-000000\r\nM000103/M000103-000001\r\n'
    assert cache.get(wait_for_value=False) == 'M000103/M000103-000001'

    first_file = pl.Path(server_root_path.name, 'M000103/M000103-000000')
    second_file = pl.Path(server_root_path.name, 'M000103/M000103-000001')
    with pan_tadeusz_file.open('rb') as pan_tadeusz:
        pan_tadeusz_2000_bytes = pan_tadeusz.read(2000)
    assert first_file.read_bytes() == pan_tadeusz_2000_bytes[:1000]
    assert second_file.read_bytes() == pan_tadeusz_2000_bytes


def test_two_decreasing_length(server_root_path, cache, reader_two_decreasing, mock_outstream, pan_tadeusz_file):
    file, out_writer = mock_outstream

    processor = ServerProtocolProcessor.ServerProtocolProcessor(reader_two_decreasing, out_writer,
                                                                cache, server_root_path.name)

    with pytest.raises(RuntimeError):
        processor.run()

    assert 'M000104' in os.listdir(server_root_path.name)

    file.seek(0)
    assert file.read() == b'\r\nM000104/M000104-000000\r\nM000104/M000104-000001\r\n'
    assert cache.get(wait_for_value=False) == 'M000104/M000104-000001'

    first_file = pl.Path(server_root_path.name, 'M000104/M000104-000000')
    second_file = pl.Path(server_root_path.name, 'M000104/M000104-000001')
    with pan_tadeusz_file.open('rb') as pan_tadeusz:
        pan_tadeusz_2000_bytes = pan_tadeusz.read(2000)
    assert first_file.read_bytes() == pan_tadeusz_2000_bytes
    assert second_file.read_bytes() == pan_tadeusz_2000_bytes[:1000]


def test_no_cache_update(server_root_path, cache, reader_two_no_cache_update, mock_outstream, pan_tadeusz_file):
    file, out_writer = mock_outstream

    processor = ServerProtocolProcessor.ServerProtocolProcessor(reader_two_no_cache_update, out_writer,
                                                                cache, server_root_path.name)

    with pytest.raises(RuntimeError):
        processor.run()

    assert 'M000105' in os.listdir(server_root_path.name)

    file.seek(0)
    assert file.read() == b'\r\nM000105/M000105-000001\r\nM000105/M000105-000000\r\n'
    assert cache.get(wait_for_value=False) == 'M000105/M000105-000001'

    first_file = pl.Path(server_root_path.name, 'M000105/M000105-000000')
    second_file = pl.Path(server_root_path.name, 'M000105/M000105-000001')
    with pan_tadeusz_file.open('rb') as pan_tadeusz:
        pan_tadeusz_100_bytes = pan_tadeusz.read(100)
    assert first_file.read_bytes() == pan_tadeusz_100_bytes
    assert second_file.read_bytes() == pan_tadeusz_100_bytes


def test_predefined_cache_value(server_root_path, cache, reader_two_no_cache_update, mock_outstream, pan_tadeusz_file):
    file, out_writer = mock_outstream

    cache.put('M000105/M000105-000003')
    processor = ServerProtocolProcessor.ServerProtocolProcessor(reader_two_no_cache_update, out_writer,
                                                                cache, server_root_path.name)

    with pytest.raises(RuntimeError):
        processor.run()

    file.seek(0)
    assert file.read() == b'M000105/M000105-000003\r\nM000105/M000105-000001\r\nM000105/M000105-000000\r\n'
    assert cache.get(wait_for_value=False) == 'M000105/M000105-000003'
