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
        self.setup_pollers()

        initialized = [False]

        def accept_action(cli, buf):
            shouldexit = [False]

            def _handler():
                if not initialized[0]:
                    initialized[0] = True
                    self.stdin.send(b"CLIENT_READY")  # ready
                    self.stdin.recv()  # server is ready

                text = buf.text.strip("\n").rstrip()
                if text:
                    buf.cursor_position = len(text)
                    buf.text = text
                    buf.reset(append_to_history=True)
                cli.output.write("\n")

                self.stdin.send(text.encode("utf-8"))
                result = self.wait_until_ready(cli)
                shouldexit[0] = not result
                return result

            cli.run_in_terminal(_handler, render_cli_done=True, raw_mode=True)

            if shouldexit[0]:
                cli.exit()

        cli = create_r_repl(accept_action)
        cli.run()
        self.control.send(b"SIGQUIT")
        self.shell.close()
        self.stdin.close()
        self.iopub.close()
        self.control.close()
        self.context.term()

    def setup_pollers(self):
        self.busy_poller = zmq.Poller()
        self.busy_poller.register(sys.stdin.fileno(), zmq.POLLIN)
        self.busy_poller.register(self.stdin, zmq.POLLIN)
        self.busy_poller.register(self.iopub, zmq.POLLIN)
        self.busy_poller.register(self.control, zmq.POLLIN)

    def wait_until_ready(self, cli):
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
                if output == b"SERVER_DEAD":
                    return False
                else:
                    sys.stdout.write(output.decode("utf-8"))

            elif self.stdin in readers:
                self.stdin.recv()  # server is ready
                break

        return True
