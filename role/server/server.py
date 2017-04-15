import zmq
import os
import signal
import threading

from . import proxy
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


def run(ports):
    context = zmq.Context()

    ports["shell_back_port"], ports["stdin_back_port"], ports["control_back_port"] = free_ports(3)

    shell = context.socket(zmq.REP)
    shell.connect("tcp://127.0.0.1:{}".format(ports["shell_back_port"]))

    stdin = context.socket(zmq.REQ)
    stdin.connect("tcp://127.0.0.1:{}".format(ports["stdin_back_port"]))

    iopub = context.socket(zmq.PUB)
    iopub.bind("tcp://127.0.0.1:{}".format(ports["iopub_port"]))

    proxy.run(context, ports)

    rinstance = Rinstance()
    api.rinstance = rinstance

    def get_text():
        stdin.send(b"ready")
        reply = stdin.recv()
        return reply.decode("utf-8")

    rinstance.read_console = create_read_console(get_text)

    def send_io(request):
        iopub.send(request.encode("utf-8"))

    rinstance.write_console_ex = create_write_console_ex(send_io)

    def control_select():
        control = context.socket(zmq.REP)
        control.connect("tcp://127.0.0.1:{}".format(ports["control_back_port"]))
        while True:
            if zmq.select([control], [], [])[0]:
                request = control.recv()
                control.send(b"ack")
                if request == b"SIGTERM":
                    os.kill(os.getpid(), signal.SIGTERM)
                elif request == b"SIGINT":
                    os.kill(os.getpid(), signal.SIGINT)

    threading.Thread(target=control_select).start()

    # rinstance.polled_events = event_callback

    rinstance.run()
    context.destroy()
