import sqlite3
import time
import csv
import sys


def main():
    while True:
        try:
            with sqlite3.connect(sys.argv[1]) as con, open(sys.argv[2], 'a') as fd:
                ((count,),) = con.execute("SELECT count(*) FROM queue").fetchall()
                writer = csv.writer(fd, delimiter=',')
                writer.writerow([time.strftime("%Y/%m/%d %H:%M:%S"), count])
        except Exception as e:
            print(e)
        finally:
            time.sleep(float(sys.argv[3]))

main()
