from multiprocessing import Process
import optparse
import signal

from . import server
from . import client


def connection_ports(ports):
    if not ports:
        ports = server.free_ports(5)
    return {
        "shell_port": ports[0],
        "iopub_port": ports[1],
        "stdin_port": ports[2],
        "control_port": ports[3],
        "hb_port": ports[4]
    }


def run():

    parser = optparse.OptionParser()
    parser.add_option('--ports')
    parser.add_option('--server-only', action="store_false", default=True, dest="run_client")
    parser.add_option('--client-only', action="store_false", default=True, dest="run_server")
    options, remainder = parser.parse_args()

    ports = connection_ports(options.ports.split(",") if options.ports else None)

    # signal.signal(signal.SIGINT, signal.SIG_IGN)

    if options.run_server:
        server_process = Process(target=server.run, args=(ports,))
        server_process.start()

    if options.run_client:
        client.run(ports, options.run_server)
