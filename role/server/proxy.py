import zmq
from threading import Thread


def shell_proxy_server(context, ports):
    shell_frontend = context.socket(zmq.ROUTER)
    shell_frontend.bind("tcp://127.0.0.1:{}".format(ports["shell_port"]))
    shell_backend = context.socket(zmq.DEALER)
    shell_backend.bind("tcp://127.0.0.1:{}".format(ports["shell_back_port"]))
    zmq.device(zmq.QUEUE, shell_frontend, shell_backend)


def stdin_proxy_server(context, ports):
    stdin_frontend = context.socket(zmq.DEALER)
    stdin_frontend.bind("tcp://127.0.0.1:{}".format(ports["stdin_port"]))
    stdin_backend = context.socket(zmq.ROUTER)
    stdin_backend.bind("tcp://127.0.0.1:{}".format(ports["stdin_back_port"]))
    zmq.device(zmq.QUEUE, stdin_frontend, stdin_backend)


def control_proxy_server(context, ports):
    control_frontend = context.socket(zmq.ROUTER)
    control_frontend.bind("tcp://127.0.0.1:{}".format(ports["control_port"]))
    control_backend = context.socket(zmq.DEALER)
    control_backend.bind("tcp://127.0.0.1:{}".format(ports["control_back_port"]))
    zmq.device(zmq.QUEUE, control_frontend, control_backend)


def run(context, ports):

    stdin_proxy = Thread(target=shell_proxy_server, args=(context, ports,))
    stdin_proxy.start()

    stdin_proxy = Thread(target=stdin_proxy_server, args=(context, ports,))
    stdin_proxy.start()

    control_proxy = Thread(target=control_proxy_server, args=(context, ports,))
    control_proxy.start()
