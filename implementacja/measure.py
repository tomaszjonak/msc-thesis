import sqlite3
import time
import csv
import sys
import pathlib as pl


def main():
    quque_path = pl.Path(sys.argv[1])
    log_path = pl.Path(sys.argv[2])
    while True:
        try:
            with sqlite3.connect(str(quque_path)) as con, log_path.open('w') as fd:
                ((count,),) = con.execute("SELECT count(*) FROM queue").fetchall()
                writer = csv.writer(fd, delimiter=',')
                writer.writerow([time.strftime("%Y/%m/%d %H:%M:%S"), count, quque_path.stat().st_size])
        except Exception as e:
            print(e)
        finally:
            time.sleep(float(sys.argv[3]))

main()
