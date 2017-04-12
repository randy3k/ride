from multiprocessing.sharedctypes import Synchronized
from multiprocessing import Queue
from multiprocessing.connection import Listener
import threading

from . import api
from .runtime import Rinstance
from .callbacks import create_read_console, create_write_console_ex


def run(host='localhost', port=0):

    rinstance = Rinstance()
    api.rinstance = rinstance
    if isinstance(port, Synchronized):
        _port = port.value
    else:
        _port = port

    listener = Listener((host, _port))

    if isinstance(port, Synchronized):
        port.value = listener.address[1]

    conn = listener.accept()

    receiveq = Queue()
    sendq = Queue()

    def get_requests_in_thread():
        while True:
            request = conn.recv()
            receiveq.put(request.decode("utf-8"))

    threading.Thread(target=get_requests_in_thread).start()

    def send_requests_in_thread():
        while True:
            conn.send(sendq.get().encode("utf-8"))

    threading.Thread(target=send_requests_in_thread).start()

    def request_getter():
        sendq.put("<ready>")
        request = receiveq.get()
        return request

    rinstance.read_console = create_read_console(request_getter)

    def request_sender(request):
        sendq.put(request)

    rinstance.write_console_ex = create_write_console_ex(request_sender)

    rinstance.run()
