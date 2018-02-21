import pathlib as pl
import sys
import datetime as dt
from collections import defaultdict
import csv


class Data(object):
    def __init__(self):
        self.avi_count = 0
        self.lvm_count = 0


def key(file: pl.Path):
    return dt.datetime.strptime(file.stem, 'M%y%m%d_%H%M%S').date()


root = pl.Path(sys.argv[1])

avi_files = root.rglob('*.avi')
lvm_files = root.rglob('*.lvm')

results = defaultdict(Data)


for file in avi_files:
    results[key(file)].avi_count += 1

for file in lvm_files:
    results[key(file)].lvm_count += 1

results = sorted(results.items(), key=lambda x: x[0])
results = ((timestamp, o.avi_count, o.lvm_count) for timestamp, o in results)

with open('daily_files.csv', 'w') as fd:
    writer = csv.writer(fd)
    writer.writerows(results)
