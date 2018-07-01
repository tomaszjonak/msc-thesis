import threading
import queue
import pathlib as pl
import datetime as dt
from ..utils import PersistentQueue

import logging
logger = logging.getLogger(__name__)


class AviFinderService(object):
    """
    Klasa odpowiedzialna za zarzadzanie watkiem zbierajacym pliki avi.
    Pozwala na uruchomienie, sprawdzenie stanu oraz zatrzymanie zarzadzanego watku
    """
    def __init__(self, avi_queue: queue.Queue, stage_queue: PersistentQueue.Queue, storage_root: pl.Path):
        self.thread = AviFinderThread(avi_queue, stage_queue, storage_root)
        logger.info("Starting avi finder service")
        self.thread.start()

    def is_ruinning(self):
        return self.thread.isAlive()

    def stop(self):
        logger.info("Stopping avi finder service")
        self.thread.stop()

    def __del__(self):
        if hasattr(self, 'thread') and self.thread:
            self.thread.join()


class AviFinderThread(threading.Thread):
    def __init__(self, avi_queue: queue.Queue, stage_queue: PersistentQueue.Queue, storage_root: pl.Path):
        self.avi_queue = avi_queue
        self.stage_queue = stage_queue
        self.storage_root = storage_root
        self.interval = 10
        self.monitoring_time = dt.timedelta(minutes=1)
        self.cont = True

        super(AviFinderThread, self).__init__()

        self.name = 'AviFinderThread'
        self.files = {}

    def run(self):
        logger.debug("main loop started")
        while self.cont:
            self.work()

    def work(self):
        try:
            new_path = self.avi_queue.get(timeout=self.interval)
            logger.debug("Adding avi path to find ({})".format(new_path))
        except:
            pass
        else:
            self.files[new_path] = dt.datetime.now()

        to_remove = []
        for path, insertion_time in self.files.items():
            if path.exists():
                relative_path = path.relative_to(self.storage_root).as_posix()
                logger.debug("Found path, pushing to queue {}".format(relative_path))
                self.stage_queue.put(relative_path)
                to_remove.append(path)
                continue

            if dt.datetime.now() - insertion_time >= self.monitoring_time:
                logger.warning("Path timed out, removing ({})".format(path))
                to_remove.append(path)
                continue

        for path in to_remove:
            del self.files[path]

    def stop(self):
        self.cont = False
