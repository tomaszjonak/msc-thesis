import sync.server.DataReceiverService as srv
import sync.utils.PersistentQueue as que

address = ('127.0.0.1', 50123)
cache = que.SqliteQueue('server.cache')
storage_root = 'server_received'

server = srv.DataReceiverServer(address=address, cache=cache, handler_cls=srv.DataReceiverHandler,
                                storage_root=storage_root)

server.serve_forever()
