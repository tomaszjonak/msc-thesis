# lzma (lzma, xz)
import lzma
# burrows wheeler (bzip2)
import bz2
# deflate (gzip) - based on lz77/lz78
import zlib

import csv
import sys
import numpy as np
import pathlib as pl
sys.path.append('.')

lvm_results_path = pl.Path('lvm_results_cut.csv')


def measure_lvm_compression(result_writer, path):
    bytes = path.read_bytes()
    data = np.loadtxt(str(path))[:, 1:]

    row = [str(path), len(bytes)]

    for compressor in (lzma.LZMACompressor(), bz2.BZ2Compressor(), zlib.compressobj()):
        result = bytearray()
        for line in data:
            byte = '{}\n'.format(','.join('{:.6f}'.format(el) for el in line)).encode()
            result += compressor.compress(byte)
        # result = compressor.compress(bytes)
        result += compressor.flush()

        row.append(len(result))

    result_writer.writerow(row)


def lvm_worker(root_path):
    with lvm_results_path.open('w') as fd:
        writer = csv.writer(fd)
        writer.writerow(['file_name', 'original_size', 'lzma', 'bz2', 'zlib'])
        files = list(root_path.rglob('*.lvm'))
        for file in files[:1000]:
            print(file)
            measure_lvm_compression(writer, file)


def main():
    if len(sys.argv) > 1:
        root_path = pl.Path(sys.argv[1])
        if not (root_path.exists() and root_path.is_dir()):
            raise FileNotFoundError(str(root_path))
    else:
        root_path = pl.Path('../client_storage/R2017_10_06')

    # lvm_worker(root_path)

main()
