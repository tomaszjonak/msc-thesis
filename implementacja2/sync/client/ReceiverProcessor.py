from ..utils import PersistentQueue
from ..utils import StreamTokenReader
import pathlib as pl


class ReceiverProcessorError(RuntimeError):
    pass


class ReceiverProcessor(object):
    def __init__(self, reader, queue, storage_root, supported_extensions):
        if not isinstance(queue, PersistentQueue.Queue):
            raise ReceiverProcessorError('Queue has to keep data despite program shutdown')

        if not isinstance(reader, StreamTokenReader.StreamTokenReader):
            raise ReceiverProcessorError('Unsupported reader type provided')

        if isinstance(storage_root, str):
            self.storage_root = pl.Path(storage_root)
        elif isinstance(storage_root, pl.Path):
            self.storage_root = storage_root
        else:
            raise ReceiverProcessorError('Unsupported storage root type ({})'.format(repr(storage_root)))

        self.queue = queue
        self.reader = reader
        self.extensions = ['.{}'.format(extension.strip('.')) for extension in supported_extensions]

    def run(self):
        while True:
            file_pattern = self.reader.get_token().decode()
            files = self.find_matching_files(file_pattern)

            file = None
            for file in files:
                self.queue.put(file)
            if file is None:
                # TODO use logger and make it warning
                print('No files matched (file_name: {}, extensions: {}'.format(file_pattern, repr(self.extensions)))

    def find_matching_files(self, file_pattern):
        base_path = pl.Path(file_pattern)
        possible_files = (base_path.with_suffix(extension) for extension in self.extensions)
        # we want to send file path relative to storage root, thus base storage_root is included
        # into path only for existence check
        return (str(file) for file in possible_files if self.storage_root.joinpath(file).exists())
