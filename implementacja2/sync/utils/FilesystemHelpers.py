import os


def count_all_files_in_filetree(path: str):
    _, _, filenames = os.walk(path).__next__()
    return len(filenames)


def get_relative_path(file, path):
    # Returns path relative to this file direcotry
    return os.path.join(os.path.dirname(file), path)


def write_all(file, buffer):
    to_write = buffer[:]
    while to_write:
        chunk_size = file.write(to_write)
        to_write = to_write[chunk_size:]
