import pytest
import pathlib as pl
import numpy as np
import datetime as dt
import itertools
import subprocess
import filecmp


def create_test_situation(client_path: str, server_path: str, client_pregenerated_files_amount: int,
                          server_storage_state: list, data_source: callable):
    current_time = dt.datetime.now()

    client_filenames = np.array([(current_time + dt.timedelta(seconds=i)).strftime('M%y%m%d/M%y%m%d-%H%M%S')
                                  for i in range(client_pregenerated_files_amount)])

    server_filenames = client_filenames[server_storage_state]

    client_paths = [pl.Path(client_path).joinpath(filename) for filename in client_filenames]
    server_paths = [pl.Path(server_path).joinpath(filename) for filename in server_filenames]

    for path in itertools.chain(client_paths, server_paths):
        path.parent.mkdir(exist_ok=True, parents=True)
        with path.open('wb') as fd:
            fd.write(data_source())

    return client_filenames


def same_contents(path1: str, path2: str):
    ret = filecmp.dircmp(path1, path2)
    decision = not (ret.right_only or ret.left_only or ret.diff_files)
    if not decision:
        ret.report()

    return decision


@pytest.fixture(scope='function')
def pan_tadeusz_source():
    def data_source():
        with open('static/pan-tadeusz-czyli-ostatni-zajazd-na-litwie.txt', 'rb') as fd:
            return fd.read()
    return data_source


class TestWithFileCleanup:
    client_path = pl.Path('client_storage')
    server_path = pl.Path('server_storage')

    def setup_method(self):
        self.client_path.mkdir(exist_ok=True, parents=True)
        self.server_path.mkdir(exist_ok=True, parents=True)

    def teardown_method(self):
        import shutil
        for path in itertools.chain(self.client_path.iterdir(), self.server_path.iterdir()):
            shutil.rmtree(str(path))

    def test_creation_sanity_equall(self, pan_tadeusz_source):
        create_test_situation(str(self.client_path), str(self.server_path), 5, [0, 1, 2, 3, 4], pan_tadeusz_source)
        assert same_contents(str(self.client_path), str(self.server_path))

    def test_creation_sanity_different(self, pan_tadeusz_source):
        create_test_situation(str(self.client_path), str(self.server_path), 5, [], pan_tadeusz_source)
        assert not same_contents(str(self.client_path), str(self.server_path))

    # def test_runtime_empty_server(self, pan_tadeusz_source):
    #     create_test_situation(str(self.client_path), str(self.server_path), 5, [], pan_tadeusz_source)
    #     assert same_contents(str(self.client_path), str(self.server_path))
