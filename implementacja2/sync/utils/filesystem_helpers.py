import os

def count_all_files_in_filetree(path: str):
    _, _, filenames = os.walk(path).__next__()
    return len(filenames)