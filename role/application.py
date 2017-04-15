from multiprocessing import Process
import optparse

from .server.util import free_ports
from .server.server import RoleServer
from .client.client import RoleClient


def connection_ports(ports):
    if not ports:
        ports = free_ports(5)
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
    parser.add_option('--server', action="store_false", default=True, dest="run_client")
    parser.add_option('--client', action="store_false", default=True, dest="run_server")
    options, remainder = parser.parse_args()

    port_dict = connection_ports(options.ports.split(",") if options.ports else None)

    if options.run_server:
        role_server = RoleServer(port_dict)
        if options.run_client:
            server_process = Process(target=role_server.run)
            server_process.start()
        else:
            print("launch client `role --client --ports={},{},{},{},{}`".format(
                port_dict["shell_port"],
                port_dict["iopub_port"],
                port_dict["stdin_port"],
                port_dict["control_port"],
                port_dict["hb_port"]))
            role_server.run()

    if options.run_client:
        role_client = RoleClient(port_dict)
        role_client.run()
