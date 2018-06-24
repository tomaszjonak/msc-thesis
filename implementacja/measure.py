import sqlite3
import time
import csv


def main():
    while True:
        with sqlite3.connect("state_storage/stage.queue") as con, open("state_storage/queue.log", 'a') as fd:
            ((count,),) = con.execute("SELECT count(*) FROM queue").fetchall()
            writer = csv.writer(fd, delimiter=',')
            writer.writerow([time.strftime("%Y/%m/%d %H:%M:%S"), count])
        time.sleep(10)

main()
