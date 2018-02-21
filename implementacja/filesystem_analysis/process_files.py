import pathlib as pl
import datetime as dt
import csv
import sys
root = pl.Path(sys.argv[1])

avi_files = root.rglob('*.avi')
lvm_files = root.rglob('*.lvm')


def key(file: pl.Path):
    return dt.datetime.strptime(file.stem, 'M%y%m%d_%H%M%S')


def data_tuples(gen):
    for file in gen:
        yield str(key(file)), file.stat().st_size

# ('lvm_results.csv', lvm_files)
for fname, source in [('avi_results.csv', avi_files)]:
    data = data_tuples(source)

    payload = sorted(data, key=lambda x: x[0])
    payload = [(str(timestamp), size) for timestamp, size in payload]

    with open(fname, 'w') as fd:
        writer = csv.writer(fd)
        writer.writerows(payload)
