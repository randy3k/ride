import zmq
from threading import Thread

from . import api
from .runtime import Rinstance
from .callbacks import create_read_console, create_write_console_ex


def free_ports(nports):
    context = zmq.Context()
    binder = context.socket(zmq.ROUTER)
    ports = []
    for i in range(nports):
        ports.append(binder.bind_to_random_port('tcp://127.0.0.1'))
    binder.close()
    context.destroy()
    return ports


def shell_proxy_server(context, ports):
    shell_frontend = context.socket(zmq.ROUTER)
    shell_frontend.bind("tcp://127.0.0.1:{}".format(ports["shell_port"]))
    shell_backend = context.socket(zmq.DEALER)
    shell_backend.bind("tcp://127.0.0.1:{}".format(ports["shell_back_port"]))
    zmq.device(zmq.QUEUE, shell_frontend, shell_backend)


def stdin_proxy_server(context, ports):
    stdin_frontend = context.socket(zmq.DEALER)
    stdin_frontend.bind("tcp://127.0.0.1:{}".format(ports["stdin_port"]))
    stdin_backend = context.socket(zmq.ROUTER)
    stdin_backend.bind("tcp://127.0.0.1:{}".format(ports["stdin_back_port"]))
    zmq.device(zmq.QUEUE, stdin_frontend, stdin_backend)


def control_proxy_server(context, ports):
    control_frontend = context.socket(zmq.ROUTER)
    control_frontend.bind("tcp://127.0.0.1:{}".format(ports["control_port"]))
    control_backend = context.socket(zmq.DEALER)
    control_backend.bind("tcp://127.0.0.1:{}".format(ports["control_back_port"]))
    zmq.device(zmq.QUEUE, control_frontend, control_backend)


def run(ports):
    context = zmq.Context()

    ports["shell_back_port"] = free_ports(1)[0]
    ports["stdin_back_port"] = free_ports(1)[0]
    ports["control_back_port"] = free_ports(1)[0]

    stdin_proxy = Thread(target=shell_proxy_server, args=(context, ports,))
    stdin_proxy.start()

    stdin_proxy = Thread(target=stdin_proxy_server, args=(context, ports,))
    stdin_proxy.start()

    control_proxy = Thread(target=control_proxy_server, args=(context, ports,))
    control_proxy.start()

    shell = context.socket(zmq.REP)
    shell.connect("tcp://127.0.0.1:{}".format(ports["shell_back_port"]))

    stdin = context.socket(zmq.REQ)
    stdin.connect("tcp://127.0.0.1:{}".format(ports["stdin_back_port"]))

    iopub = context.socket(zmq.PUB)
    iopub.bind("tcp://127.0.0.1:{}".format(ports["iopub_port"]))

    control = context.socket(zmq.REP)
    control.connect("tcp://127.0.0.1:{}".format(ports["control_back_port"]))

    poller = zmq.Poller()
    poller.register(stdin, zmq.POLLIN)
    poller.register(control, zmq.POLLIN)

    rinstance = Rinstance()
    api.rinstance = rinstance

    def get_text():
        stdin.send(b"ready")
        while True:
            socks = dict(poller.poll())
            if stdin in socks:
                reply = stdin.recv()
                return reply.decode("utf-8")
            elif control in socks:
                request = control.recv()
                if request == b"EXIT":
                    return None

    rinstance.read_console = create_read_console(get_text)

    def send_io(request):
        iopub.send(request.encode("utf-8"))

    rinstance.write_console_ex = create_write_console_ex(send_io)

    rinstance.run()
    context.destroy()
