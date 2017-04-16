import zmq
import sys
import os

from .repl import create_r_repl
from .heartbeat import HeartBeatChannel


class RoleClient(object):

    initialized = False

    def __init__(self, ports):
        self.context = zmq.Context()
        self.ports = ports
        super(RoleClient, self).__init__()

    def connect_channels(self):
        ports = self.ports
        context = self.context

        shell = context.socket(zmq.REQ)
        shell.connect("tcp://127.0.0.1:{}".format(ports["shell_port"]))
        shell.setsockopt(zmq.LINGER, 0)

        stdin = context.socket(zmq.REQ)
        stdin.connect("tcp://127.0.0.1:{}".format(ports["stdin_port"]))
        stdin.setsockopt(zmq.LINGER, 0)

        iopub = context.socket(zmq.SUB)
        iopub.connect("tcp://127.0.0.1:{}".format(ports["iopub_port"]))
        iopub.setsockopt(zmq.LINGER, 0)
        iopub.setsockopt(zmq.SUBSCRIBE, b"")

        control = context.socket(zmq.REQ)
        control.connect("tcp://127.0.0.1:{}".format(ports["control_port"]))
        control.setsockopt(zmq.LINGER, 0)

        self.shell = shell
        self.stdin = stdin
        self.iopub = iopub
        self.control = control

    def run(self):

        self.connect_channels()
        self.heartbeat_channel = HeartBeatChannel(self.context, self.ports["hb_port"])
        self.heartbeat_channel.start()
        self.setup_pollers()

        cli = create_r_repl(self.accept_action)
        cli.run()

        # todo: move to cli.on_exit
        self.control.send(b"SIGQUIT")
        self.shell.close()
        self.stdin.close()
        self.iopub.close()
        self.control.close()
        self.heartbeat_channel.close()
        self.context.term()

    def setup_pollers(self):
        self.busy_poller = zmq.Poller()
        self.busy_poller.register(sys.stdin.fileno(), zmq.POLLIN)
        self.busy_poller.register(self.stdin, zmq.POLLIN)
        self.busy_poller.register(self.iopub, zmq.POLLIN)
        self.busy_poller.register(self.control, zmq.POLLIN)

    def accept_action(self, cli, buf):
        if not self.initialized:
            self.initialized = True
            self.stdin.send(b"CLIENT_READY")  # ready
            self.stdin.recv()  # server is ready

        text = buf.text.strip("\n").rstrip()
        if text:
            buf.cursor_position = len(text)
            buf.text = text
            buf.reset(append_to_history=True)

        self.stdin.send(text.encode("utf-8"))
        retcode = self.wait_until_ready()
        return retcode

    def wait_until_ready(self):
        sigint_is_pending = False
        while True:
            if not self.heartbeat_channel.is_beating():
                return 1

            readers = dict(self.busy_poller.poll(100))

            if self.control in readers:
                # get any ack reply from control channel
                self.control.recv()
                if sigint_is_pending:
                    sigint_is_pending = False

            elif sys.stdin.fileno() in readers:
                key = os.read(sys.stdin.fileno(), 1024)
                if b"\x03" in key and not sigint_is_pending:
                    sys.stdout.write("^C")
                    self.control.send(b"SIGINT")
                    sigint_is_pending = True

            elif self.iopub in readers:
                output = self.iopub.recv()
                sys.stdout.write(output.decode("utf-8"))

            elif self.stdin in readers:
                self.stdin.recv()  # server is ready
                break

        return 0
