from ..utils import PersistentQueue
from ..utils import StreamTokenReader
import pathlib as pl
import logging

logger = logging.getLogger(__name__)


class ReceiverProcessorError(RuntimeError):
    pass


class ReceiverProcessor(object):
    def __init__(self, reader, queue, storage_root, supported_extensions, sync_queue=None):
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
        self.sync_queue = sync_queue
        self.reader = reader
        self.extensions = ['.{}'.format(extension.strip('.')) for extension in supported_extensions]

        self.cont = True

        self.operation = self._process_files
        # self.operation = self._get_first_record if self.sync_queue else self._process_files

    def _get_first_record(self):
        file_pattern = self.reader.get_token().decode()
        files = self.find_matching_files(file_pattern)

        if not files:
            logger.warning('No files matched (file_name: {}, extensions: {}'
                           .format(file_pattern, repr(self.extensions)))
            return

        # first_received = min((self.storage_root.joinpath(file) for file in files),
        #                      key=lambda file: file.stat().st_ctime_ns)

        # try:
        #     self.sync_queue.put(first_received)
        # except Exception as e:
        #     print(repr(e))

        for file in files:
            self.queue.put(file)

        self.operation = self._process_files

    def run(self):
        while self.cont:
            try:
                self.operation()
            except TimeoutError:
                logger.info('Receiver processor timeout')
            except Exception as e:
                logger.exception(e)
                raise

    def _process_files(self):
        file_pattern = self.reader.get_token().decode()
        files = self.find_matching_files(file_pattern)
        logger.debug('Found matching files ({})'.format(len(files)))

        file = None
        for file in files:
            logger.debug('Adding file to queue ({})'.format(file))
            self.queue.put(file)
        if file is None:
            # TODO use logger and make it warning
            logger.warning('No files matched (file_name: {}, extensions: {}'
                           .format(file_pattern, repr(self.extensions)))

    def find_matching_files(self, file_pattern):
        base_path = pl.Path(file_pattern)
        logger.debug('Base path: {}'.format(base_path))
        possible_files = (base_path.with_suffix(extension) for extension in self.extensions)
        # we want to send file path relative to storage root, thus base storage_root is included
        # into path only for existence check
        return [file.as_posix() for file in possible_files if self.storage_root.joinpath(file).exists()]

    def stop(self):
        self.reader.timeout = 1
        self.cont = False
