import pathlib
import subprocess
import logging
import os

logger = logging.getLogger(__name__)

ffmpeg_path = os.environ.get("FFMPEG_PATH", "ffmpeg")
try:
    subprocess.check_call([ffmpeg_path, "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
except subprocess.CalledProcessError:
    logger.error("Bad ffmpeg path provided, set FFMPEG_PATH env variable to proper value")
    exit(-1)


# TODO rewrite with some form of piping instead of buffer file
class Compressor(object):
    def __init__(self, ffmpeg_path):
        self.ffmpeg = ffmpeg_path

        try:
            subprocess.check_call([ffmpeg_path, '-version'], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        except subprocess.CalledProcessError as e:
            logger.error('Provided path to ffmpeg cli is invalid ({})'.format(ffmpeg_path))
            raise

        self.temp_path = pathlib.Path('temp.mp4')

    def __call__(self, file, preset='slow', crf=32, *args, **kwargs):
        if self.temp_path.exists():
            self.temp_path.unlink()

        create_cmd = [ffmpeg_path, '-i', str(file),
                      '-preset', preset,
                      '-crf', str(crf),
                      '-c:v', 'libx264',
                      str(self.temp_path)]

        subprocess.check_call(create_cmd, stderr=subprocess.DEVNULL)
        bytes_ = self.temp_path.read_bytes()
        self.temp_path.unlink()
        return bytes_


def compress(file: pathlib.Path, preset='veryslow', crf=32):
    temp_path = pathlib.Path('temp.mp4')
    if temp_path.exists():
        temp_path.unlink()

    create_cmd = ['ffmpeg', '-i', str(file),
                  '-preset', preset,
                  '-crf', str(crf),
                  '-c:v', 'libx264',
                  str(temp_path)]

    subprocess.check_call(create_cmd, stderr=subprocess.DEVNULL)
    bytes = temp_path.read_bytes()
    temp_path.unlink()
    return bytes


def map_extension(original):
    return '.mp4'
