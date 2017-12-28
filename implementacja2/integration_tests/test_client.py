import pytest
import time
import contextlib
import pathlib as pl

from ..sync.client import SenderService
from ..sync.client import ReceiverService
from ..sync.labview_sim import feeder_service
from ..sync.utils import PersistentQueue
from ..sync.utils import contexts as ctx
from ..sync.utils import StreamProxy, StreamTokenReader, StreamTokenWriter


# I must admit raii is easier here
@contextlib.contextmanager
def connection_accepedetd(conn_params):
    conn, _ = conn_params
    yield conn
    conn.close()


def test_creation(labview_address, server_address, storage_root, queue_file, client_sync_queue, server_sync_queue):
    feeder_srv = feeder_service.FeederContorller(storage_root=storage_root, address=labview_address,
                                                 queue_timeout=0.5)
    sender_queue_view = PersistentQueue.SqliteQueue(queue_file)
    sender_srv = SenderService.SenderService(storage_root=storage_root, address=server_address,
                                             stage_queue=sender_queue_view, sync_queue=server_sync_queue,
                                             retry_time=0.5)

    receiver_queue_view = PersistentQueue.SqliteQueue(queue_file)
    receiver_srv = ReceiverService.ReceiverService(storage_root=storage_root, address=labview_address,
                                                   stage_queue=receiver_queue_view, sync_queue=client_sync_queue,
                                                   retry_time=0.5)

    sender_srv.stop()
    feeder_srv.stop()
    receiver_srv.stop()


def token_ops_from_connection(connection):
    stream = StreamProxy.SocketStreamProxy(connection)
    writer = StreamTokenWriter.StreamTokenWriter(stream, '\r\n')
    reader = StreamTokenReader.StreamTokenReader(stream, '\r\n')
    return reader, writer


def test_context(client_context):
    with ctx.listener_context(client_context.server_address) as listener:
        with connection_accepedetd(listener.accept()) as conn:
            reader, writer = token_ops_from_connection(conn)
            writer.write_token('')
            file_pattern = client_context.feeder_srv.create_and_announce_dated_files()
            file_read = reader.get_token().decode()
            file = client_context.storage_root.joinpath(file_read)
            assert file.relative_to(client_context.storage_root).with_suffix('') == pl.Path(file_pattern)
            assert file.exists()
            assert file.is_file()
            size_read = int(reader.get_token())
            assert file.stat().st_size == size_read
            assert file.read_bytes() == reader.get_bytes(30)
            writer.write_token(file_read)
