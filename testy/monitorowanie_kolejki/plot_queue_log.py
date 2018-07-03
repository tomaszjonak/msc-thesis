import sys
import pandas as pd
import subprocess
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

retrieve_command = [
    'ssh', '-A', 'tomaszjonak@traffic.eu.org', 'rsync -avz gardawice:/cygdrive/e/RejGARD/sender/queue.log .',
    '&&',
    'rsync', '-avz', 'tomaszjonak@traffic.eu.org:', 'queue.log', '.'
]


def main():
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        # path = "queue_0107.log"
        path = "queue.log"
        # subprocess.check_call(retrieve_command)

    data = pd.read_csv(path, index_col=0, parse_dates=True, header=None)
    data.rename(columns={1: "Ilosc plikow do wyslania"}, inplace=True)
    data.index.name = "Czas pomiaru"

    matplotlib.style.use('ggplot')

    fig, ax = plt.subplots()

    data['Ilosc plikow do wyslania'].plot(ax=ax)
    # ax.yaxis.lim(ymin=0)
    ax.set_title("Dlugosc kolejki plikow do wyslania")
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    ax.xaxis.set_minor_locator(mdates.HourLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('\n%d/%m'))
    ax.xaxis.set_minor_formatter(mdates.DateFormatter('%H'))
    ax.xaxis.grid(b=True, which='major', linewidth=2)
    ax.xaxis.grid(b=True, which='minor')
    ax.set_ylim(bottom=0)

    fig, ax = plt.subplots()

    (data[2]/1000).plot(ax=ax)
    # ax.yaxis.lim(ymin=0)
    ax.set_title("Wielkosc pliku kolejki")
    # ax.xaxis.label = "Wielkosc pliku kolejki w kilobajtach"
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    ax.xaxis.set_minor_locator(mdates.HourLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('\n%d/%m'))
    ax.xaxis.set_minor_formatter(mdates.DateFormatter('%H'))
    ax.xaxis.grid(b=True, which='major', linewidth=2)
    ax.xaxis.grid(b=True, which='minor')
    ax.set_ylim(bottom=0)

    plt.tight_layout()
    plt.show()

main()
