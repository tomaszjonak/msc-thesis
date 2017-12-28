import sync.server.DataReceiverService as srv
import sync.utils.PersistentQueue as que
import pathlib as pl
import logging

logger = logging.getLogger(__name__)


def main():
    logger.info('Setting up server')
    config = {
        'host': '127.0.0.1',
        'port': 50123,
        'cache_path': 'state_storage/server.cache',
        'storage_root': 'state_storage/server_storage_root'
    }
    address = config['host'], int(config['port'])
    cache_path = pl.Path(config['cache_path'])
    if cache_path.parent.exists() and not cache_path.parent.is_dir():
        logger.error('Cache file parent directory is not a directory (you can use nonexistent dir instead)')
        exit(-1)
    cache_path.parent.mkdir(exist_ok=True, parents=True)
    cache = que.SqliteQueue(str(cache_path))

    storage_root = pl.Path(config['storage_root'])
    if storage_root.parent.exists() and not storage_root.parent.is_dir():
        logger.error('Storage root dir has to be nested under directory (current parent is not a directory)')
        exit(-1)
    storage_root.parent.mkdir(exist_ok=True, parents=True)

    server = srv.DataReceiverServer(address=address, cache=cache, handler_cls=srv.DataReceiverHandler,
                                    storage_root=storage_root)

    logger.info('Listening {}'.format(address))
    server.serve_forever()


main()
