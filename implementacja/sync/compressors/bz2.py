import bz2


def compress(file):
    file_bytes = file.read_bytes()
    return bz2.compress(file_bytes)


def map_extension(original):
    return original + '.bz2'


def remap_extension(received):
    if len(received) > 1:
        res = received[:-1]
    else:
        res = received

    return ''.join(res)


def decompress(bytestream):
    return bz2.decompress(bytestream)
