import threading
import socket
import time
import logging
logger = logging.getLogger(__name__)


class KeepAliveWorker(threading.Thread):
    """
    Class responsible for establishing, keeping alive and reestablishing connection to remote host

    Workflow: subclass this one and provide `work` method which operates on active connection
    """
    def __init__(self, config):
        self.address = config["host"], int(config["port"])
        self.connection_retry_interval = int(config['connection_retry_interval'])

        self.socket = None
        self.operation = self._try_establishing
        self.work = self.work or None
        if not callable(self.work):
            raise RuntimeError("No workload specified")
        super(KeepAliveWorker, self).__init__()

    def run(self):
        while True:
            self.operation()

    def _try_establishing(self):
        try:
            self.socket = socket.create_connection(self.address)
        except (ConnectionRefusedError, ConnectionError):
            logger.warning('Connection refused, sleeping...')
            time.sleep(self.connection_retry_interval)
        else:
            logger.info('Connection to {} established'.format(self.address))
            self.operation = self._op

    def _op(self):
        try:
            self.work()
        except (ConnectionAbortedError, BrokenPipeError, ConnectionError) as e:
            logger.warning("Lost connection".format(repr(e)))
            logger.debug("{}".format(repr(e)))
            self.socket.close()
            time.sleep(self.connection_retry_interval)
            self.operation = self._try_establishing
