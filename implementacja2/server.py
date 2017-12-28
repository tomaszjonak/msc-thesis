#!/usr/bin/env python

import sync.server.DataReceiverService as srv

import pathlib as pl
import argparse
import json
import logging

logger = logging.getLogger(__name__)


def main():
    logger.info('Setting up server')
    config = {
        'host': '127.0.0.1',
        'port': 50123,
        'storage_root': 'server_storage'
    }

    parser = argparse.ArgumentParser(description='TODO make some description')
    parser.add_argument('--config', '-c', action='store', help='json format config '
                                                               'default one will be dumped to debug logs')
    parser.add_argument('--options', '-o', action='append', nargs=2, metavar=('config.part.field', 'value'),
                        help='this can be used multiple times to override config options (experimental, does not work'
                             ' with compound values i.e nested dicts or lists)')

    args = parser.parse_args()

    if args.config:
        logger.info('Pulling configuration from file (./{})'.format(args.config))
        with open(args.config, 'r') as fd:
            config = json.load(fd)
    else:
        logger.info('Using hardcoded configuration')

    # Loop below overrides values in config based on scope
    # i.e providing -o Sender.host 192.168.0.1 results in
    # config['Sender']['host'] = '192.168.0.1'
    # TODO: duplcates code from client.py - do i want separation or code reuse
    for scope_str, value in args.options or []:
        scope = scope_str.split('.')
        curr = config
        try:
            for config_part in scope[:-1]:
                curr = config[config_part]
            curr[scope[-1]] = value
        except KeyError as e:
            print('Undefined config section (section: {}, tag: {}, value: {})'
                  .format(e, repr(scope_str), value))
            exit(-1)

    logger.debug('Configuration state\n{}'.format(json.dumps(config, indent=2)))

    address = config['host'], int(config['port'])
    storage_root = pl.Path(config['storage_root'])
    if storage_root.parent.exists() and not storage_root.parent.is_dir():
        logger.error('Storage root dir has to be nested under directory (current parent is not a directory)')
        exit(-1)
    storage_root.parent.mkdir(exist_ok=True, parents=True)

    server = srv.DataReceiverServer(address=address, handler_cls=srv.DataReceiverHandler,
                                    storage_root=storage_root)

    logger.info('Listening {}'.format(address))
    server.serve_forever()


main()
