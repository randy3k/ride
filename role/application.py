import zmq
from multiprocessing import Process
from .server import server
from .client import client


def free_ports(nports):
    context = zmq.Context()
    binder = context.socket(zmq.ROUTER)
    ports = []
    for i in range(nports):
        ports.append(binder.bind_to_random_port('tcp://127.0.0.1'))
    binder.close()
    return ports


def connection_ports():
    ports = free_ports(5)
    return {
        "shell_port": ports[0],
        "iopub_port": ports[1],
        "stdin_port": ports[2],
        "control_port": ports[3],
        "hb_port": ports[4]
    }


def run():
    ports = connection_ports()

    p = Process(target=server.run, args=(ports,))
    p.start()

    client.run(ports)
    p.terminate()
