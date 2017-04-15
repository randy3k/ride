import zmq
import os
import signal
import threading

from .util import free_ports
from .proxy import run_proxy
from .runtime import api
from .runtime.instance import Rinstance
from .runtime.callbacks import create_read_console, create_write_console_ex


class RoleServer(object):

    def __init__(self, ports):
        self.context = zmq.Context()
        self.ports = ports
        super(RoleServer, self).__init__()

    def connect_channels(self):
        ports = self.ports
        context = self.context

        shell = context.socket(zmq.REP)
        shell.connect("tcp://127.0.0.1:{}".format(ports["shell_back_port"]))

        stdin = context.socket(zmq.REQ)
        stdin.connect("tcp://127.0.0.1:{}".format(ports["stdin_back_port"]))

        iopub = context.socket(zmq.PUB)
        iopub.bind("tcp://127.0.0.1:{}".format(ports["iopub_port"]))

        self.shell = shell
        self.stdin = stdin
        self.iopub = iopub

        self.connect_control_channel()

    def connect_control_channel(self):

        def _control_thread():
            control = self.context.socket(zmq.REP)
            control.connect("tcp://127.0.0.1:{}".format(self.ports["control_back_port"]))
            control_poller = zmq.Poller()
            control_poller.register(control, zmq.POLLIN)
            while True:
                if control_poller.poll():
                    request = control.recv()
                    control.send(b"ack")
                    if request == b"SIGTERM":
                        os.kill(os.getpid(), signal.SIGTERM)
                    elif request == b"SIGINT":
                        os.kill(os.getpid(), signal.SIGINT)

        threading.Thread(target=_control_thread).start()

    def setup_rinstance(self):

        api.rinstance = self.rinstance

        initialized = [False]

        def get_text():
            if not initialized[0]:
                initialized[0] = True
            self.stdin.send(b"ready")
            reply = self.stdin.recv()
            return reply.decode("utf-8")

        self.rinstance.read_console = create_read_console(get_text)

        def print_text(text):
            self.iopub.send(text.encode("utf-8"))

        self.rinstance.write_console_ex = create_write_console_ex(print_text)

    def run(self):
        ports = self.ports
        (ports["shell_back_port"],
         ports["stdin_back_port"],
         ports["control_back_port"]) = free_ports(3)

        run_proxy(self.context, self.ports)
        self.connect_channels()

        self.rinstance = Rinstance()
        self.setup_rinstance()

        # run the r eventloop
        self.rinstance.run()
        self.context.term()
