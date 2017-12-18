import implementacja2.sync.client.ReceiverService as receiver
import implementacja2.sync.client.SenderService as sender
import implementacja2.sync.utils.PersistentQueue as que
import pathlib

server_address = ('192.168.100.101', 50123)
storage_root = pathlib.Path('client_storage')
storage_root.mkdir(exist_ok=True, parents=True)
queue = que.SqliteQueue('client.db')
cache = que.SqliteQueue('client.cache')


sender_service = sender.SenderService(address=server_address, storage_root=storage_root,
                                      stage_queue=queue, sync_queue=None)

labview_address = ('127.0.0.1', 50321)
receiver_service = receiver.ReceiverService(labview_address, queue, storage_root, cache)
