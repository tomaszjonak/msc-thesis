import datetime as dt
import pathlib as pl
import os


class DatedFilesGenerator(object):
    def __init__(self, storage_root, file_fmt, dir_fmt, **kwargs):
        self.storage_root = storage_root if isinstance(storage_root, pl.Path) else pl.Path(storage_root)
        self.file_fmt = file_fmt
        self.dir_fmt = dir_fmt
        self.root_timestamp = dt.datetime.now()

        self.file_size = kwargs.get('file_size', 30)
        self.extensions = kwargs.get('extensions', ['avi, lvm'])

        self.file_offset = 0
        self.dir_offset = 0

    def generate_file(self, content=None, extensions=None):
        content = content or os.urandom(self.file_size)
        extensions = extensions or self.extensions

        date = self.root_timestamp + dt.timedelta(days=self.dir_offset, seconds=self.file_offset)
        file_name_base = '{}/{}'.format(date.strftime(self.dir_fmt), date.strftime(self.file_fmt))
        file_base = self.storage_root.joinpath(file_name_base)
        for extension in extensions:
            file = file_base.with_suffix('.{}'.format(extension))
            file.parent.mkdir(exist_ok=True, parents=True)
            file.write_bytes(content)

        self.file_offset += 1
        return file_name_base

    def next_directory(self, n=1):
        self.dir_offset += n

