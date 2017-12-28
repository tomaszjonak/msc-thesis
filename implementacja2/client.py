import sync.client.ReceiverService as receiver
import sync.client.SenderService as sender
import sync.utils.PersistentQueue as que
import sync.client.SynchronizationService as sc

import pathlib
import queue
import argparse
import logging
import signal


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
    # Using same sqlite connection from multiple threads fails miserably, thus 3 'views'
    stage_queue_view1 = que.SqliteQueue(stage_queue_path)
    stage_queue_view2 = que.SqliteQueue(stage_queue_path)
    stage_queue_view3 = que.SqliteQueue(stage_queue_path)

    cache = que.SqliteQueue(config['cache_path'])

    services = []

    # def sigint_handler(signum, frame):
    #     # TODO add timeouts to config
    #     # logger.info('SIGINT trapped, services may take some time to shut down (if too long send few more sigints)')
    #     logger.info('Gracefull shutdown is not yet supported, send sigint few more times (ctrl+c)')
    #     [service.stop() for service in services]
    #
    # signal.signal(signal.SIGINT, sigint_handler)

    sync_queue = queue.Queue()
    logger.info('Starting synchronization service')
    sync_service = sc.SynchronizationService(sync_queue=sync_queue, queue_view=stage_queue_view2,
                                             storage_root=storage_root)
    services.append(sync_service)

    labview_address = (config['provider']['host'], int(config['provider']['port']))
    logger.info('Starting receiver service')
    receiver_service = receiver.ReceiverService(labview_address, stage_queue_view3, storage_root,
                                                cache, sync_queue, extensions=config['provider']['extensions'],
                                                separator=config['provider']['separator'])
    services.append(receiver_service)

    server_address = (config['server']['host'], int(config['server']['port']))
    logger.info('Starting sender service')
    sender_service = sender.SenderService(address=server_address, storage_root=storage_root,
                                          stage_queue=stage_queue_view1, sync_queue=None)
    services.append(sender_service)


main()
