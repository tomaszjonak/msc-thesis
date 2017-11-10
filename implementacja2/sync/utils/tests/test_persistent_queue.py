import pytest
import tempfile
import os
from .. import PersistentQueue


@pytest.fixture(scope='function')
def db_path(request):
    fd, path = tempfile.mkstemp()
    file = open(fd)

    def finalizer():
        file.close()
        os.remove(path)

    request.addfinalizer(finalizer)
    return path


def test_empty(queue):
    assert not queue.get(wait_for_value=False)


def test_put(queue):
    assert queue.len() == 0
    queue.put(1)
    assert queue.len() == 1


def test_pop(queue):
    queue.put(1)
    element = queue.get()
    assert element == '1'


def test_pop_put_sequence(queue):
    queue.put(1)
    queue.put(2)
    queue.put(3)
    assert queue.len() == 3
    element = queue.get()
    assert element == '1'
    assert queue.len() == 3
    queue.pop(element)
    assert queue.len() == 2
    assert queue.get() == '2'


def test_persistence(directory_path):
    file = str(directory_path.joinpath('example.db'))
    queue1 = PersistentQueue.SqliteQueue(file)
    queue1.put(1)
    del queue1
    queue2 = PersistentQueue.SqliteQueue(file)
    assert queue2.len() == 1
    assert queue2.get() == '1'


def test_sqlite_lifo(queue):
    import time
    queue.set_order(order='LIFO')
    for number in range(5):
        # Delay due to timestamp resolution in sqlite (damned thing)
        time.sleep(0.01)
        queue.put(str(number))

    for number in reversed(range(5)):
        result = queue.get()
        queue.pop(result)
        assert int(result) == number


def test_sqlite_fifo(queue):
    queue.set_order(order='FIFO')

    for number in range(5):
        queue.put(str(number))

    for number in range(5):
        result = queue.get()
        queue.pop(result)
        assert int(result) == number
