import pathlib
import itertools
import sys
import tarfile


def get_size_and_count(tar_paths):
    """
    :param tar_paths: list/generator of pathlib.Path objects
    :return:
    """
    size = 0
    count = 0
    tarfiles = [tarfile.open(str(path)) for path in tar_paths]
    file_infos = (tfile.getmembers() for tfile in tarfiles)
    for info_pack in file_infos:
        foo = [info for info in info_pack if info.isfile()]
        tar_size = sum(info.size for info in foo)
        tar_count = len(foo)

        size += tar_size
        count += tar_count

    return count, size


path = pathlib.Path(sys.argv[1])

folders = (file.iterdir() for file in path.iterdir()
           if file.is_dir)

files = (file for file in itertools.chain(*folders))
bzip_files = path.glob('*.tar.bz2')

bytes_count = 0
files_count = 0

