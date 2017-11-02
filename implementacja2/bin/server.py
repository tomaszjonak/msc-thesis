try:
    from sync import utils
    from sync.server import DataReceiverService
except ImportError:
    import sys
    sys.path.append('..')
    from sync import utils
    from sync.server import DataReceiverService


import sys

if len(sys.argv) < 4:
    print('not enough arguments')
    exit(-1)

host, port = sys.argv[1].split(':')
address = host, int(port)
storage_root = sys.argv[2]
cache_file_path = sys.argv[3]

service = DataReceiverService.DataReceiverService(address, storage_root, cache_file_path)
