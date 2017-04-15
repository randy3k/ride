import zmq
import sys
import os
import time

from prompt_toolkit.utils import suspend_to_background_supported

from .repl import create_r_repl


def run(ports, server_is_running):
    context = zmq.Context()

    shell = context.socket(zmq.REP)
    shell.connect("tcp://127.0.0.1:{}".format(ports["shell_port"]))

    stdin = context.socket(zmq.REP)
    stdin.connect("tcp://127.0.0.1:{}".format(ports["stdin_port"]))

    iopub = context.socket(zmq.SUB)
    iopub.connect("tcp://127.0.0.1:{}".format(ports["iopub_port"]))
    iopub.setsockopt(zmq.SUBSCRIBE, b"")

    control = context.socket(zmq.REQ)
    control.connect("tcp://127.0.0.1:{}".format(ports["control_port"]))

    stdin_poller = zmq.Poller()
    stdin_poller.register(stdin, zmq.POLLIN)
    iopub_poller = zmq.Poller()
    iopub_poller.register(iopub, zmq.POLLIN)

    initalized = [False]

    def on_accept_action(cli):
        if not initalized[0]:
            initalized[0] = True
            stdin.recv()  # ready

        text = cli.current_buffer.text.strip("\n").rstrip()
        if text:
            cli.current_buffer.cursor_position = len(text)
            cli.current_buffer.text = text
            cli.current_buffer.reset(append_to_history=True)
        cli.output.write("\n")

        stdin.send(text.encode("utf-8"))

        while True:
            readers, _, _ = zmq.select([sys.stdin.fileno(), stdin, iopub], [], [])
            if sys.stdin.fileno() in readers:
                key = os.read(sys.stdin.fileno(), 1024)
                if b"\x03" in key:
                    sys.stdout.write("^C")
                    control.send(b"SIGINT")
                    control.recv()  # wait for sigint

            if iopub in readers:
                stime = time.time()
                while iopub_poller.poll(0) and time.time() - stime < 1:
                    output = iopub.recv()
                    sys.stdout.write(output.decode("utf-8"))
            if stdin in readers:
                stdin.recv()  # wait until next ready
                break

    cli = create_r_repl(on_accept_action)

    cli.run()
    control.send(b"SIGTERM")
    context.destroy()
