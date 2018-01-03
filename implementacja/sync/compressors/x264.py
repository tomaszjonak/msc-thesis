import pathlib
import subprocess


# TODO rewrite with some form of piping instead of buffer file
def compress(file: pathlib.Path, preset='slow', crf=32):
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
