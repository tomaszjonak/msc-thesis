import pytest
import pathlib as pl

from ...utils import StreamProxy
from ...utils import StreamTokenReader
from ...utils import FilesystemHelpers as fsh
from .. import ServerProtocolProcessor as spp


def get_vector_reader(vector_path):
    full_path = fsh.get_relative_path(__file__, vector_path)
    stream = StreamProxy.FileStreamProxy(full_path)
    return StreamTokenReader.StreamTokenReader(stream, b'\r\n')


def test_vector(server_root_path, mock_outstream, vector_description):
    file, out_writer = mock_outstream

    vector_reader = get_vector_reader(vector_description.vector_path)
    processor = spp.ServerProtocolProcessor(vector_reader, out_writer, server_root_path.name)

    with pytest.raises(BrokenPipeError):
        processor.run()

    file.seek(0)
    assert vector_description.token_sequence.encode() == file.read()

    storage_root = server_root_path.name
    for file_group_description in vector_description.file_groups:
        source_path = file_group_description.source_path
        source_file = pl.Path(fsh.get_relative_path(__file__, source_path))
        source_bytes = source_file.read_bytes()
        for file_state in file_group_description.file_states:
            expected_file = pl.Path(storage_root, file_state.path)
            assert expected_file.read_bytes() == source_bytes[:file_state.size]
