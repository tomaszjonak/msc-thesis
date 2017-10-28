import os


def count_all_files_in_filetree(path: str):
    _, _, filenames = os.walk(path).__next__()
    return len(filenames)


def get_relative_path(name):
    # Returns path relative to this file direcotry
    return os.path.join(os.path.dirname(__file__), name)
