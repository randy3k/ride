import zmq
import sys
import signal

from .repl import create_r_repl


def run(ports):
    signal.signal(signal.SIGINT, signal.SIG_IGN)

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

    def on_accept_action(text):
        if not initalized[0]:
            initalized[0] = True
            stdin.recv()  # ready

        stdin.send(text.encode("utf-8"))
        while True:
            while iopub_poller.poll(0):
                output = iopub.recv()
                sys.stdout.write(output.decode("utf-8"))
            if stdin_poller.poll(0):
                stdin.recv()  # wait until next ready
                break

    cli = create_r_repl(on_accept_action)
    cli.run()
    control.send(b"EXIT")
    context.destroy()
