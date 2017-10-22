import sqlite3
import logging
logger = logging.getLogger(__name__)


class ObservedFiles(object):
    def __init__(self, db_name=None):
        db_name = db_name or 'example.db'
        self.conn = sqlite3.connect(db_name)

    def add(self, filename):
        """
        Adds filename to observed files
        :param filename: str
        """
        try:
            with self.conn as cn:
                cn.execute('INSERT INTO observed_files VALUES (?)', (filename,))
        except sqlite3.Error as e:
            logger.exception(e)

    def remove(self, filename):
        """
        Removes filename from observed files
        :param filename:
        """
        try:
            with self.conn as cn:
                cn.execute('DELETE FROM observed_files WHERE filepath=?', (filename,))
        except sqlite3.Error as e:
            logger.exception(e)

    def get_all(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT filepath FROM observed_files')
        data = cursor.fetchall()
        return data

    def clear(self):
        try:
            with self.conn as cn:
                cn.execute('DELETE FROM observed_files')
        except sqlite3.Error as e:
            logger.exception(e)


def sample_run():
    of = ObservedFiles()
    of.clear()
    of.add('top.kek')
    data = of.get_all()
    print(repr(data))
    of.add('bar.baz')
    data = of.get_all()
    print(repr(data))
    of.remove('top.kek')
    data = of.get_all()
    print(repr(data))


if __name__ == '__main__':
    FORMAT = '%(asctime)s [%(name)s|%(threadName)s] %(levelname)s: %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.DEBUG)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    sample_run()
