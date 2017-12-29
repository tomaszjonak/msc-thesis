#!/usr/bin/env python
import argparse
import subprocess
import pathlib as pl
import logging
import multiprocessing
import time


logger = logging.getLogger(__name__)


def ffmpeg_present():
    try:
        subprocess.check_call(['ffmpeg', '-version'], stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return False
    return True


def create_mp4(avi_file, preset, crf):
    result_path = avi_file.with_suffix('.mp4')
    if result_path.exists():
        result_path.unlink()

    create_cmd = ['ffmpeg', '-i', str(avi_file),
                  '-preset', preset,
                  '-crf', str(crf),
                  '-c:v', 'libx264',
                  str(result_path)]
    subprocess.check_call(create_cmd, stderr=subprocess.DEVNULL)


async def compress_file_coroutine(file_path, delete_original=False):
    create_mp4(file_path, 'slow', 32)
    if delete_original:
        file_path.unlink()


class Compressor(object):
    def __init__(self, preset, crf, delete_original=False):
        self.preset = preset
        self.crf = crf
        self.delete_original = delete_original

    def __call__(self, file_path, *args, **kwargs):
        create_mp4(file_path, self.preset, self.crf)
        if self.delete_original:
            file_path.unlink()


def main():
    fmt = '%(asctime)s [%(levelname)s]: %(message)s'
    logging.basicConfig(level=logging.INFO, format=fmt)

    if not ffmpeg_present:
        logger.error('No ffmpeg installed, couldn\'t proceed')
        exit(-1)

    parser = argparse.ArgumentParser(description='Tool for compressing avi files into mp4 using x264 codec. '
                                                 'Be mindful this just searches based on file suffix (avi)')
    parser.add_argument('--starting_folder', '-s', action='store', required=True, help='folder to search files from')
    parser.add_argument('--delete_original', action='store_true', help='Removes avi files after mp4 creation')
    parser.add_argument('--crf', action='store', type=int, help='Constant Ratio Factor value', default=32)
    parser.add_argument('--preset', action='store', help='ffmpeg preset', default='slow')

    args = parser.parse_args()

    if args.preset not in ('ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 'medium', 'slow', 'veryslow'):
        logger.error('Unsupported ffmpeg preset used ({})'.format(args.preset))
        exit(-1)

    if args.crf not in range(53):
        logger.error('Invalid crf value provided ({})'.format(args.crf))
        exit(-1)

    root_folder = pl.Path(args.starting_folder)
    files_to_compress = list(root_folder.rglob('*.avi'))
    if not files_to_compress:
        logger.warning('Found no avi files under given folder ({})'.format(args.starting_folder))
        exit(0)
    else:
        logger.info('Found {} files, starting compression'.format(len(files_to_compress)))

    compressor = Compressor(args.preset, args.crf, args.delete_original)

    start = time.time()
    with  multiprocessing.Pool() as pool:
        [pool.apply_async(compressor, [file_path]) for file_path in files_to_compress]
        pool.close()
        pool.join()
    end = time.time()

    logger.info('Compression done ({:.4} s)'.format(end - start))


main()
