from ..utils import PersistentQueue
from ..utils import StreamTokenReader
import pathlib as pl
import logging

logger = logging.getLogger(__name__)


class ReceiverProcessorError(RuntimeError):
    pass


class ReceiverProcessor(object):
    def __init__(self, reader, queue, storage_root, supported_extensions, cache, sync_queue=None):
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
        self.cache = cache
        self.sync_queue = sync_queue
        self.reader = reader
        self.extensions = ['.{}'.format(extension.strip('.')) for extension in supported_extensions]

        self.cont = True

        # self.operation = self._process_files
        self.operation = self._get_first_record if self.sync_queue else self._process_files

    def _get_first_record(self):
        file_pattern = self.reader.get_token().decode()
        files, first_received, last_received = self.find_matching_files(file_pattern)

        if not files:
            logger.warning('No files matched (file_name: {}, extensions: {}'
                           .format(file_pattern, repr(self.extensions)))
            return

        cached_file = self.cache.instant_get()
        self.cache.pop(cached_file)
        self.cache.put(last_received.relative_to(self.storage_root).as_posix())

        if cached_file:
            cached_file = self.storage_root.joinpath(cached_file)
            try:
                self.sync_queue.put((cached_file, first_received, self.queue.get_all()))
                logger.info('Triggered synchronization job')
            except Exception as e:
                logger.exception(e)
        else:
            logger.info('No cached values found, skipping synchronization')

        for file in files:
            self.queue.put(file)

        self.operation = self._process_files

    def run(self):
        while self.cont:
            try:
                self.operation()
            except TimeoutError:
                logger.debug('Receiver processor timeout')
            except Exception as e:
                logger.exception(e)
                raise

    def _process_files(self):
        file_pattern = self.reader.get_token().decode()
        try:
            files, _, newest_file = self.find_matching_files(file_pattern)
        except ValueError:
            logger.warning('No files found for given pattern ({})'.format(file_pattern))
            return

        newest_relative_path = newest_file.relative_to(self.storage_root).as_posix()

        logger.debug('Found matching files ({})'.format(len(files)))
        last = self.cache.instant_get()
        if not last:
            logger.warning('Unexpected empty cache in regular processing')
            logger.debug('Updating cache ({})'.format(newest_relative_path))
        else:
            logger.debug('Updating cache (was: {}, new: {})'.format(last, newest_relative_path))
            self.cache.pop(last)
        self.cache.put(newest_relative_path)

        file = None
        for file in files:
            logger.debug('Adding file to queue ({})'.format(file))
            self.queue.put(file)
        if file is None:
            logger.warning('No files matched (file_name: {}, extensions: {}'
                           .format(file_pattern, repr(self.extensions)))

    def find_matching_files(self, file_pattern):
        base_path = pl.Path(file_pattern)
        logger.debug('Base path: {}'.format(base_path))
        possible_files = (base_path.with_suffix(extension) for extension in self.extensions)
        # we want to send file path relative to storage root, thus base storage_root is included
        # into path only for existence check
        full_paths = (self.storage_root.joinpath(file) for file in possible_files)
        valid_paths = [path for path in full_paths if path.exists()]
        if not valid_paths:
            return [], None, None
        last_created = max(valid_paths, key=lambda file: file.stat().st_ctime_ns)
        first_created = min(valid_paths, key=lambda file: file.stat().st_ctime_ns)
        return [path.relative_to(self.storage_root).as_posix() for path in valid_paths], last_created, first_created

    def stop(self):
        self.reader.timeout = 1
        self.cont = False
