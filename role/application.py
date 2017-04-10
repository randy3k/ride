from prompt_toolkit import prompt
from prompt_toolkit.utils import Event

import threading

from multiprocessing.connection import Listener, Client
from multiprocessing.sharedctypes import Synchronized
from multiprocessing import Process, Value
try:
    from queue import Queue
except:
    from Queue import Queue
import time

from .server.runtime import Rinstance
from .server.callbacks import create_read_console
from .server import api

from .client.repl import create_r_repl


def run_server(host='localhost', port=0, authkey=b'role+application'):
    rinstance = Rinstance()
    api.rinstance = rinstance
    if isinstance(port, Synchronized):
        _port = port.value
    else:
        _port = port

    q = Queue()

    listener = Listener((host, _port), authkey=authkey)
    if isinstance(port, Synchronized):
        port.value = listener.address[1]

    conn = listener.accept()

    def get_requests_in_thread():
        while True:
            request = conn.recv()
            q.put(request)

    threading.Thread(target=get_requests_in_thread).start()

    def request_getter():
        # prompt is ready
        conn.send("<ready>")
        request = q.get()
        return request

    rinstance.read_console = create_read_console(request_getter)

    rinstance.run()


def run_client(host='localhost', port=0, authkey=b'role+application'):
    conn = Client(('localhost', port), authkey=authkey)
    conn.recv()  # ready

    def request_sender(request):
        conn.send(request)
        conn.recv()  # ready

    cli = create_r_repl(request_sender)

    cli.run()


def main():
    port = Value("i", 0)
    p = Process(target=run_server, kwargs={"port": port})
    p.start()

    while True:
        if port.value != 0:
            break
        time.sleep(0.2)

    run_client(port=port.value)
    p.join()
