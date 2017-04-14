import zmq
import sys
import signal

from .repl import create_r_repl


def run(ports):
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    context = zmq.Context()
    stdin = context.socket(zmq.REP)
    stdin.bind("tcp://*:{}".format(ports["stdin_port"]))

    iopub = context.socket(zmq.SUB)
    iopub.connect("tcp://localhost:{}".format(ports["iopub_port"]))
    iopub.setsockopt(zmq.SUBSCRIBE, b"")

    poller = zmq.Poller()
    poller.register(stdin, zmq.POLLIN)
    poller.register(iopub, zmq.POLLIN)

    initalized = [False]

    def handle_request(request):
        if not initalized[0]:
            initalized[0] = True
            stdin.recv()  # ready

        stdin.send(request.encode("utf-8"))

        while True:
            socks = dict(poller.poll())
            if iopub in socks and socks[iopub] == zmq.POLLIN:
                output = iopub.recv()
                sys.stdout.write(output.decode("utf-8"))
            if stdin in socks and socks[stdin] == zmq.POLLIN:
                stdin.recv()  # wait until next ready
                break
        while poller.poll(1):
            output = iopub.recv()
            sys.stdout.write(output.decode("utf-8"))

    cli = create_r_repl(handle_request)
    cli.run()
