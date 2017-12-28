import pytest
import tempfile
import pathlib as pl
import queue
import collections


from ..sync.client import SenderService
from ..sync.client import ReceiverService
from ..sync.labview_sim import feeder_service
from ..sync.utils import PersistentQueue


@pytest.fixture(scope='function')
def client_sync_queue():
    return queue.Queue()


@pytest.fixture(scope='function')
def server_sync_queue():
    return queue.Queue()


@pytest.fixture(scope='function')
def storage_root():
    dir = tempfile.TemporaryDirectory()
    storage_root = pl.Path(dir.name)
    yield storage_root
    dir.cleanup()


@pytest.fixture(scope='function')
def queue_file():
    file = tempfile.NamedTemporaryFile(delete=False)
    yield file.name
    file.delete = True
    file.close()


@pytest.fixture(scope='function')
def labview_address():
    return '127.0.0.1', 20010


@pytest.fixture(scope='function')
def server_address():
    return '127.0.0.1', 20011


@pytest.fixture(scope='function')
def client_context(labview_address, server_address, storage_root, queue_file, client_sync_queue, server_sync_queue):
    feeder_srv = feeder_service.FeederContorller(
        storage_root=storage_root,
        address=labview_address,
        queue_timeout=0.5
    )

    sender_queue_view = PersistentQueue.SqliteQueue(queue_file)
    sender_srv = SenderService.SenderService(
        storage_root=storage_root,
        address=server_address,
        stage_queue=sender_queue_view,
        sync_queue=server_sync_queue,
        retry_time=0.5
    )

    receiver_queue_view = PersistentQueue.SqliteQueue(queue_file)
    receiver_srv = ReceiverService.ReceiverService(
        storage_root=storage_root,
        address=labview_address,
        stage_queue=receiver_queue_view,
        sync_queue=client_sync_queue,
        retry_time=0.5
    )

    fields = (
        'sender_srv',
        'receiver_srv',
        'feeder_srv',
        'storage_root',
        'labview_address',
        'server_address',
        'client_sync_queue',
        'server_sync_queue',
        'extensions'
    )
    Context = collections.namedtuple('Context', fields)
    ctx = Context(
        sender_srv=sender_srv,
        receiver_srv=receiver_srv,
        feeder_srv=feeder_srv,
        storage_root=storage_root,
        labview_address=labview_address,
        server_address=server_address,
        client_sync_queue=client_sync_queue,
        server_sync_queue=server_sync_queue,
        extensions=['lvm', 'avi']
    )

    yield ctx

    sender_srv.stop()
    feeder_srv.stop()
    receiver_srv.stop()
