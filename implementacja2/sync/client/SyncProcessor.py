import pathlib as pl
import itertools


class SyncProcessor(object):
    def __init__(self, queue_view, storage_root: pl.Path, extensions, staged_files):
        self.queue = queue_view
        self.storage_root = storage_root
        self.extensions = extensions
        self.staged_files = staged_files

    def update_queue(self, server_info, client_info):
        upper_time = client_info.lstat().st_ctime_ns
        lower_time = server_info.lstat().st_ctime_ns
        possible_matches = self.find_files_in_time_span(lower_time, upper_time)
        matches = (file for file in possible_matches if file not in self.staged_files)
        for file in matches:
            self.queue.put(str(file.relative_to(self.storage_root)))

    def find_files_in_time_span(self, lower, upper):
        """
        :param lower: timestamp najstarszego interesujacego pliku
        :param upper: timestamp najmlodszego interesujacego pliku
        :return:
        """
        # Warto zauwazyc ze ustalanie interesujacego timestampu jest za pomoca ostrej nierownosci
        # poslugujemy sie unix time
        directories = (file for file in self.storage_root.iterdir()
                       if file.is_dir()) # and lower < file.lstat().st_ctime_ns < upper)
        # there should be sane way to pick catalogues just from given day
        # but its pretty deep into internal structure of produced data
        files_in_root_dir = (file for file in self.storage_root.iterdir()
                             if not file.is_dir() and lower < file.lstat().st_ctime_ns < upper
                             and file.suffix.strip('.') in self.extensions)

        files = files_in_root_dir
        for directory, extension in itertools.product(directories, self.extensions):
            suspect_files = (file for file in directory.rglob('*.{}'.format(extension))
                             if lower < file.lstat().st_ctime_ns < upper)
            files = itertools.chain(files, suspect_files)

        return files
