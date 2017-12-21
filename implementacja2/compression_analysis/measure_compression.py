# Schematy

# csv
#   falki
#   bezstratne (idealnie bezstratny plus ffmpeg na video)

# Video:
#   ffmpeg z driverem x264
#   ffmpeg z driverem x265
import subprocess
#   Jakis inny

# Bezstratne
# lzma (lzma, xz)
import lzma
# burrows wheeler (bzip2)
import bz2
# deflate (gzip) - based on lz77/lz78
import zlib

# Zbior testowy
# dane z jednego dnia


# Ustawienia ffmpga
# preset (ultrafast to veryslow)
# tune (sprawdzic czy w ogole warto)
# crf

import csv
import sys
import pathlib as pl
sys.path.append('..')
from sync.wavelet_compression import wavelet_lvm


def measure_lvm_compression(result_writer, path):
    bytes = path.read_bytes()

    row = [str(path), len(bytes)]

    for compressor in (lzma.LZMACompressor(), bz2.BZ2Compressor(), zlib.compressobj()):
        result = compressor.compress(bytes)
        result += compressor.flush()

        row.append(len(result))

    wavelet_len = len(wavelet_lvm.encode_file(path))
    row.append(wavelet_len)

    result_writer.writerow(row)


def calculate_ffmpeg_size(avi_file, preset, crf):
    test_path = pl.Path('test.mp4')
    if test_path.exists():
        test_path.unlink()

    create_cmd = ['ffmpeg', '-i', str(avi_file),
                  '-preset', preset,
                  '-crf', str(crf),
                  '-c:v', 'libx264',
                  str(test_path)]
    subprocess.check_call(create_cmd, stderr=subprocess.DEVNULL)
    size = test_path.stat().st_size
    test_path.unlink()

    return size


def measure_avi_compression(result_writer, path):
    bytes = path.read_bytes()

    row = [str(path), len(bytes)]
    for compressor in (lzma.LZMACompressor(), bz2.BZ2Compressor(), zlib.compressobj()):
        result = compressor.compress(bytes)
        result += compressor.flush()

        row.append(len(result))

    row.append(calculate_ffmpeg_size(path, 'slow', '32'))
    print(row)
    result_writer.writerow(row)


def main():
    if len(sys.argv) > 1:
        root_path = pl.Path(sys.argv[1])
        if not (root_path.exists() and root_path.is_dir()):
            raise FileNotFoundError(str(root_path))
    else:
        root_path = pl.Path('../client_storage/R2017_10_06')

    # lvm_results_path = pl.Path('lvm_results.csv')
    # with lvm_results_path.open('w') as fd:
    #     writer = csv.writer(fd)
    #     writer.writerow(['file_name', 'original_size', 'lzma', 'bz2', 'zlib', 'wavelets'])
    #     files = list(root_path.rglob('*.lvm'))
    #     for file in files:
    #         measure_lvm_compression(writer, file)

    avi_results_path = pl.Path('avi_results.csv')
    with avi_results_path.open('w') as fd:
        writer = csv.writer(fd)
        writer.writerow(['file_name', 'original_size', 'lzma', 'bz2', 'zlib', 'x264'])
        files = list(root_path.rglob('*.avi'))
        print('Analysing {} files'.format(len(files)))
        for file in files:
            measure_avi_compression(writer, file)


main()
