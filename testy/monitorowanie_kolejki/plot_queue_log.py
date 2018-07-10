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
        path = "sym_wavelets_12kbps.log"
        # subprocess.check_call(retrieve_command)

    data = pd.read_csv(path, index_col=0, parse_dates=True, header=None)
    data.rename(columns={1: "Ilosc plikow do wyslania"}, inplace=True)
    data.index.name = "Czas pomiaru"

    matplotlib.style.use('ggplot')
    matplotlib.rcParams.update({'font.size': 20})

    fig, ax = plt.subplots()

    data['Ilosc plikow do wyslania'].iloc[::2].plot(ax=ax)
    # ax.yaxis.lim(ymin=0)
    ax.set_title("Wielkosc kolejki plikow do wyslania w czasie dzialania aplikacji")
    ax.set_xlabel("Godzina")
    ax.set_ylabel("Ilosc plikow oczekujacych na wyslanie")
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    # ax.xaxis.set_minor_locator(mdates.HourLocator(byhour=range(0, 24, 2)))
    ax.xaxis.set_minor_locator(mdates.HourLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('\n%d/%m'))
    ax.xaxis.set_minor_formatter(mdates.DateFormatter('%H'))
    ax.xaxis.grid(b=True, which='major', linewidth=2)
    ax.xaxis.grid(b=True, which='minor')
    ax.set_ylim(bottom=0, top=5)

    # fig, ax = plt.subplots()

    # (data[2]/1000).plot(ax=ax)
    # ax.set_title("Wielkosc pliku kolejki")
    # ax.set_ylabel("Wielkosc pliku kolejki w kilobajtach")
    # ax.set_xlabel("Godzina")
    # ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    # ax.xaxis.set_minor_locator(mdates.HourLocator(byhour=range(0, 24, 2)))
    # ax.xaxis.set_major_formatter(mdates.DateFormatter('\n%d/%m'))
    # ax.xaxis.set_minor_formatter(mdates.DateFormatter('%H'))
    # ax.xaxis.grid(b=True, which='major', linewidth=2)
    # ax.xaxis.grid(b=True, which='minor')
    # ax.set_ylim(bottom=0)

    # plt.tight_layout()
    plt.show()

main()
