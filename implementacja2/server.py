import implementacja2.sync.server.DataReceiverService as srv
import implementacja2.sync.utils.PersistentQueue as que

address = ('127.0.0.1', 50123)
cache = que.SqliteQueue('cache.db')
storage_root = 'server_received'

server = srv.DataReceiverServer(address=address, cache=cache, handler_cls=srv.DataReceiverHandler,
                                storage_root=storage_root)

server.serve_forever()
