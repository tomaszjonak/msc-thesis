import pathlib as pl
from pprint import pprint
import numpy as np
from sync.wavelet_compression import wavelet_lvm


def get_file_pairs(client_storage, server_storage, extension):
    relative_paths = [path.relative_to(server_storage) for path in server_storage.rglob('*.{}'.format(extension))]
    file_pairs = [(client_storage.joinpath(path), server_storage.joinpath(path)) for path in relative_paths]
    invalid_paths = [path for _, path in file_pairs if not path.exists()]
    return file_pairs, invalid_paths


def analyse_file_pair(client_file, server_file):
    pass


def main():
    client_storage = pl.Path('client_storage')
    server_storage = pl.Path('server_received')

    pairs, invalid_paths = get_file_pairs(client_storage, server_storage, 'lvm')

    pprint(pairs)
    pprint(invalid_paths)


main()
