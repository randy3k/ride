import zmq


def free_ports(nports):
    context = zmq.Context()
    binder = context.socket(zmq.ROUTER)
    ports = []
    for i in range(nports):
        ports.append(binder.bind_to_random_port('tcp://127.0.0.1'))
    binder.close()
    context.destroy()
    return ports
