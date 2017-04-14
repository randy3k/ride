import zmq

from . import api
from .runtime import Rinstance
from .callbacks import create_read_console, create_write_console_ex


def run(ports):
    context = zmq.Context()
    stdin = context.socket(zmq.REQ)
    stdin.connect("tcp://localhost:{}".format(ports["stdin_port"]))

    iopub = context.socket(zmq.PUB)
    iopub.bind("tcp://*:{}".format(ports["iopub_port"]))

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

    rinstance.run()
