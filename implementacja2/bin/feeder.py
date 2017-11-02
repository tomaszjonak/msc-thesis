try:
    from sync import utils
    from sync.labview_sim import feeder_service
except ImportError:
    import sys
    sys.path.append('..')
    from sync import utils
    from sync.labview_sim import feeder_service

service = None


def start_service(*args):
    global service
    service = feeder_service.FeederContorller()


def stop_service(*args):
    global service
    if service:
        service.stop()
    service = None


def announce(*args):
    global service
    if not service:
        print('You have to start service first')
    else:
        service.announce_file(args[0])


def noop(*args):
    print('No such command')


def quit(*args):
    global service
    if service:
        service.stop()
    exit()

ops = {
    'start': start_service,
    'stop': stop_service,
    'announce': announce,
    'q': quit
}

while True:
    ctrl = input('>>> ').split()
    if not ctrl:
        continue
    op, args = ctrl[0], ctrl[1:]
    ops.get(op, noop)(*args)
