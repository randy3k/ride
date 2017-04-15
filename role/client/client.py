import zmq
import sys
import os

from .repl import create_r_repl


class RoleClient(object):

    def __init__(self, ports):
        self.context = zmq.Context()
        self.ports = ports
        super(RoleClient, self).__init__()

    def connect_channels(self):
        ports = self.ports
        context = self.context

        shell = context.socket(zmq.REP)
        shell.connect("tcp://127.0.0.1:{}".format(ports["shell_port"]))

        stdin = context.socket(zmq.REP)
        stdin.connect("tcp://127.0.0.1:{}".format(ports["stdin_port"]))

        iopub = context.socket(zmq.SUB)
        iopub.connect("tcp://127.0.0.1:{}".format(ports["iopub_port"]))
        iopub.setsockopt(zmq.SUBSCRIBE, b"")

        control = context.socket(zmq.REQ)
        control.connect("tcp://127.0.0.1:{}".format(ports["control_port"]))

        self.shell = shell
        self.stdin = stdin
        self.iopub = iopub
        self.control = control

    def run(self):

        self.connect_channels()
        self.setup_pollers()

        initalized = [False]

        def on_accept_action(cli):
            if not initalized[0]:
                initalized[0] = True
                self.stdin.recv()  # ready

            text = cli.current_buffer.text.strip("\n").rstrip()
            if text:
                cli.current_buffer.cursor_position = len(text)
                cli.current_buffer.text = text
                cli.current_buffer.reset(append_to_history=True)
            cli.output.write("\n")

            self.stdin.send(text.encode("utf-8"))
            self.wait_until_ready()

        cli = create_r_repl(on_accept_action)

        cli.run()
        self.control.send(b"SIGTERM")
        self.context.term()

    def setup_pollers(self):
        self.busy_poller = zmq.Poller()
        self.busy_poller.register(sys.stdin.fileno(), zmq.POLLIN)
        self.busy_poller.register(self.stdin, zmq.POLLIN)
        self.busy_poller.register(self.iopub, zmq.POLLIN)
        self.busy_poller.register(self.control, zmq.POLLIN)

    def wait_until_ready(self):
        sigint_is_pending = False
        while True:
            readers = dict(self.busy_poller.poll())
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
                self.stdin.recv()  # wait until next ready
                break
