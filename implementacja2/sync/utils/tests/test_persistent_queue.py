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


@pytest.fixture(scope='function')
def queue_factory(db_path):
    def factory():
        return PersistentQueue.SqliteQueue(db_path)
    return factory


def test_put(queue_factory):
    queue = queue_factory()
    assert queue.len() == 0
    queue.put(1)
    assert queue.len() == 1


def test_pop(queue_factory):
    queue = queue_factory()
    queue.put(1)
    element = queue.get()
    assert element == '1'


def test_pop_put_sequence(queue_factory):
    queue = queue_factory()
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


def test_persistence(queue_factory):
    queue = queue_factory()
    queue.put(1)
    del queue
    queue = queue_factory()
    assert queue.len() == 1
    assert queue.get() == '1'
