import sync.client.ReceiverService as receiver
import sync.client.SenderService as sender
import sync.utils.PersistentQueue as que
import sync.client.SynchronizationService as sc

import pathlib
import queue
import argparse
import logging


logger = logging.getLogger(__name__)


def main():
    logger.info('Setting up client')
    config = {
        'server': {
            'host': '127.0.0.1',
            'port': 50123
        },
        'provider': {
            'host': '127.0.0.1',
            'port': 50321,
            'extensions': ['lvm', 'avi'],
            'retry_time': 30,
            'separator': '\n'
        },
        'storage_root': 'client_storage',

        'stage_queue_path': 'state_storage/stage.queue',
        'cache_path': 'state_storage/client.cache'
    }


    storage_root = pathlib.Path(config['storage_root'])
    if storage_root.parent.exists() and not storage_root.parent.is_dir():
        logger.error('')
    storage_root.mkdir(exist_ok=True, parents=True)

    stage_queue_path = config['stage_queue_path']
    stage_queue_view1 = que.SqliteQueue(stage_queue_path)
    stage_queue_view2 = que.SqliteQueue(stage_queue_path)
    stage_queue_view3 = que.SqliteQueue(stage_queue_path)

    cache = que.SqliteQueue(config['cache_path'])

    sync_queue = queue.Queue()
    logger.info('Starting synchronization service')
    sync_service = sc.SynchronizationService(sync_queue=sync_queue, queue_view=stage_queue_view2,
                                             storage_root=storage_root)

    labview_address = (config['provider']['host'], int(config['provider']['port']))
    logger.info('Starting receiver service')
    receiver_service = receiver.ReceiverService(labview_address, stage_queue_view3, storage_root,
                                                cache, sync_queue, extensions=config['provider']['extensions'],
                                                separator=config['provider']['separator'])

    server_address = (config['server']['host'], int(config['server']['port']))
    logger.info('Starting sender service')
    sender_service = sender.SenderService(address=server_address, storage_root=storage_root,
                                          stage_queue=stage_queue_view1, sync_queue=None)


main()
