import pathlib as pl
import subprocess
import sys
import time
import csv
import itertools
import multiprocessing


def calculate_ffmpeg_size_time(avi_file: pl.Path, preset, crf):
    test_path = pl.Path('{}_{}_{}.mp4'.format(avi_file.name, preset, crf))

    create_cmd = ['ffmpeg', '-i', str(avi_file),
                  '-preset', preset,
                  '-crf', str(crf),
                  '-c:v', 'libx264',
                  str(test_path)]
    begin = time.time()
    subprocess.check_call(create_cmd, stderr=subprocess.DEVNULL)
    end = time.time()
    size = test_path.stat().st_size
    test_path.unlink()

    return size, end - begin


def worker_function(params):
    file, preset = params
    compressed_size, compression_time = calculate_ffmpeg_size_time(file, preset, 32)
    return file.name, preset, file.stat().st_size, compressed_size, compression_time


def main():
    root_path = pl.Path(sys.argv[1])
    if not root_path.exists() and root_path.is_dir():
        exit(-1)
    print(root_path)

    avi_files = root_path.rglob('*.avi')

    presets = [
        'ultrafast',
        'superfast',
        'veryfast',
        'faster',
        'fast',
        'medium',
        'slow',
        'slower',
        'veryslow',
    ]

    with open('x264_params.csv', 'w') as fd:
        writer = csv.writer(fd)
        writer.writerow(['file','preset','original_size','compressed_size','compression_time'])
        pool = multiprocessing.Pool(multiprocessing.cpu_count())

        results = pool.map(worker_function, itertools.product(avi_files, presets))
        for result in results:
            writer.writerow(result)

main()
