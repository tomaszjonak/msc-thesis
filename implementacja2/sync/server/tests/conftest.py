import pytest
import tempfile
import collections

from ...utils import StreamProxy
from ...utils import StreamTokenWriter
from ...utils import PersistentQueue


@pytest.fixture(scope='function')
def cache():
    f = tempfile.NamedTemporaryFile(delete=False)
    cache_instance = PersistentQueue.SqliteQueue(f.name)
    return cache_instance


@pytest.fixture(scope='function')
def server_root_path():
    path = tempfile.TemporaryDirectory()
    return path


@pytest.fixture(scope='function')
def mock_outstream():
    file = tempfile.NamedTemporaryFile()
    stream = StreamProxy.TempFileStreamProxy(file, file)
    writer = StreamTokenWriter.StreamTokenWriter(stream, '\r\n')

    return file, writer


# TODO store those in json and use to generate test vectors
one_file_vector_dict = {
    'vector_path': 'vectors/one_file.vector',
    'cache_initial_state': None,
    'cache_expected_state': 'M000101/M000101-000000',
    'expected_ack_sequence': ('M000101/M000101-000000',),
    'expected_disk_state': [
        {
            'source_path': 'vectors/pan-tadeusz-czyli-ostatni-zajazd-na-litwie.txt',
            'file_states': [
                {'path': 'M000101/M000101-000000', 'size': 1000},
            ]
        }
    ]
}

two_equall_length_dict = {
    'vector_path': 'vectors/two_equall_length.vector',
    'cache_initial_state': None,
    'cache_expected_state': 'M000102/M000102-000001',
    'expected_ack_sequence': (
        'M000102/M000102-000000',
        'M000102/M000102-000001'
    ),
    'expected_disk_state': [
        {
            'source_path': 'vectors/pan-tadeusz-czyli-ostatni-zajazd-na-litwie.txt',
            'file_states': [
                {'path': 'M000102/M000102-000000', 'size': 1000},
                {'path': 'M000102/M000102-000001', 'size': 1000}
            ]
        }
    ]
}

two_increasing_length_dict = {
    'vector_path': 'vectors/two_increasing_length.vector',
    'cache_initial_state': None,
    'cache_expected_state': 'M000103/M000103-000001',
    'expected_ack_sequence': (
        'M000103/M000103-000000',
        'M000103/M000103-000001'
    ),
    'expected_disk_state': [
        {
            'source_path': 'vectors/pan-tadeusz-czyli-ostatni-zajazd-na-litwie.txt',
            'file_states': [
                {'path': 'M000103/M000103-000000', 'size': 1000},
                {'path': 'M000103/M000103-000001', 'size': 2000}
            ]
        }
    ]
}


two_decreasing_length_dict = {
    'vector_path': 'vectors/two_decreasing_length.vector',
    'cache_initial_state': None,
    'cache_expected_state': 'M000104/M000104-000001',
    'expected_ack_sequence': (
        'M000104/M000104-000000',
        'M000104/M000104-000001'
    ),
    'expected_disk_state': [
        {
            'source_path': 'vectors/pan-tadeusz-czyli-ostatni-zajazd-na-litwie.txt',
            'file_states': [
                {'path': 'M000104/M000104-000000', 'size': 2000},
                {'path': 'M000104/M000104-000001', 'size': 1000}
            ]
        }
    ]
}


two_no_cache_update_path_dict = {
    'vector_path': 'vectors/two_no_cache_update.vector',
    'cache_initial_state': None,
    'cache_expected_state': 'M000105/M000105-000001',
    'expected_ack_sequence': (
        'M000105/M000105-000001',
        'M000105/M000105-000000'
    ),
    'expected_disk_state': [
        {
            'source_path': 'vectors/pan-tadeusz-czyli-ostatni-zajazd-na-litwie.txt',
            'file_states': [
                {'path': 'M000105/M000105-000000', 'size': 100},
                {'path': 'M000105/M000105-000001', 'size': 100}
            ]
        }
    ]
}


@pytest.fixture(scope='function', params=[
    one_file_vector_dict,
    two_equall_length_dict,
    two_increasing_length_dict,
    two_decreasing_length_dict,
    two_no_cache_update_path_dict
])
def vector_description(request):
    vector_dct = request.param
    DiskStateDescription = collections.namedtuple('DiskStateDescription', ('source_path', 'file_states'))
    VectorDescription = collections.namedtuple('VectorDescription', ('vector_path', 'cache_initial',
                                                                     'cache_expected', 'token_sequence',
                                                                     'file_groups', 'ack_sequence'))
    FileStateDescription = collections.namedtuple('FileStateDescription', ('path', 'size'))

    file_groups = []
    for file_group in vector_dct['expected_disk_state']:
        path = file_group['source_path']
        file_states = [FileStateDescription(dct['path'], dct['size']) for dct in file_group['file_states']]
        file_groups.append(DiskStateDescription(path, file_states))

    cache_initial_state = vector_dct['cache_initial_state']
    ack_sequence_ = vector_dct['expected_ack_sequence']
    ack_sequence = '\r\n'.join(ack_sequence_)
    token_sequence = '{cache_initial}\r\n{ack_sequence}\r\n'.format(
        cache_initial=cache_initial_state or '',
        ack_sequence=ack_sequence
    )

    vector_description_ = VectorDescription(
        vector_path=vector_dct['vector_path'],
        cache_initial=vector_dct['cache_initial_state'],
        cache_expected=vector_dct['cache_expected_state'],
        token_sequence=token_sequence,
        file_groups=file_groups,
        ack_sequence=ack_sequence_
    )

    return vector_description_
