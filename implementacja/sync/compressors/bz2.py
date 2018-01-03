import bz2


def compress(file):
    file_bytes = file.read_bytes()
    return bz2.compress(file_bytes)


def map_extension(original):
    return original + '.bz2'
