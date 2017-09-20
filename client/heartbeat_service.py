import threading
import socket
import logging
import time

logger_name = __name__ if __name__ != '__main__' else "DataClient"
logger = logging.getLogger(logger_name)
logger.setLevel(logging.DEBUG)


class HeartBeatThread(threading.Thread):
    def __init__(self, config):
        self.host = config["server_fqdn"]
        self.port = int(config["server_port"])
        self.heartbeat_interval = int(config['heartbeat_interval'])
        self.connection_retry_interval = int(config['connection_retry_interval'])

        self.socket = None
        self.operation = self.try_establishing
        super(HeartBeatThread, self).__init__()

    def run(self):
        while True:
            self.operation()

    def try_establishing(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
        except ConnectionRefusedError:
            logger.warning('Connection refused, sleeping...')
            time.sleep(self.connection_retry_interval)
        else:
            logger.info('Connection established')
            self.operation = self.send_heartbeat

    def send_heartbeat(self):
        try:
            self.socket.send(b'x')
        except (ConnectionAbortedError, BrokenPipeError) as e:
            logger.warning("Connection aborted ({})".format(repr(e)))
            self.socket.close()
            time.sleep(self.connection_retry_interval)
            self.operation = self.try_establishing
        else:
            logger.debug("Heartbeat sent")
            time.sleep(self.heartbeat_interval)

