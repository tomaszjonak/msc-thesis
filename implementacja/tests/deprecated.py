import pathlib as pl
import itertools

client_root = pl.Path('client/data')
server_root = pl.Path('server/received')

server_first_received = client_root.joinpath('M171008/M171008-135102_0.csv')
server_last_received = client_root.joinpath('M171008/M171008-135102_1.avi')

client_first_in_new_run = client_root.joinpath('M171009/M171009-135102_1.csv')

folder_creation_time = server_last_received.parent.stat().st_ctime_ns
# print(folder_creation_time)
# print(server_last_received.stat().st_ctime_ns)
folders = (file.iterdir() for file in client_root.iterdir()
           if file.is_dir() and file.stat().st_ctime_ns >= folder_creation_time)


def make_predicate(last_synced, first_in_this_run):
    def predicate(current_file):
        ctime = current_file.stat().st_ctime_ns
        last_ctime = last_synced.stat().st_ctime_ns
        first_this_ctime = first_in_this_run.stat().st_ctime_ns
        return first_this_ctime > ctime > last_ctime
    return predicate

pred = make_predicate(server_last_received, client_first_in_new_run)

files_to_sync = (file for file in itertools.chain(*folders)
                 if pred(file))

for file in files_to_sync:
    print(str(file))