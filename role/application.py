from multiprocessing import Process
from .server import server
from .client import client


def connection_ports():
    ports = server.free_ports(5)
    return {
        "shell_port": ports[0],
        "iopub_port": ports[1],
        "stdin_port": ports[2],
        "control_port": ports[3],
        "hb_port": ports[4]
    }


def run():
    ports = connection_ports()

    server_process = Process(target=server.run, args=(ports,))
    server_process.start()

    client.run(ports)
    server_process.terminate()
