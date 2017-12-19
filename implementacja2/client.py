import sync.client.ReceiverService as receiver
import sync.client.SenderService as sender
import sync.utils.PersistentQueue as que
import sync.client.SynchronizationService as sc
import pathlib
import queue

server_address = ('127.0.0.1', 50123)
storage_root = pathlib.Path('client_storage')
storage_root.mkdir(exist_ok=True, parents=True)
stage_queue_view1 = que.SqliteQueue('client.db')
stage_queue_view2 = que.SqliteQueue('client.db')
stage_queue_view3 = que.SqliteQueue('client.db')
cache = que.SqliteQueue('client.cache')
sync_queue = queue.Queue()


sender_service = sender.SenderService(address=server_address, storage_root=storage_root,
                                      stage_queue=stage_queue_view1, sync_queue=None)

sync_service = sc.SynchronizationService(sync_queue=sync_queue, queue_view=stage_queue_view2, storage_root=storage_root)

labview_address = ('127.0.0.1', 50321)
receiver_service = receiver.ReceiverService(labview_address, stage_queue_view3, storage_root, cache, sync_queue)
