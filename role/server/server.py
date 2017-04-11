from multiprocessing.sharedctypes import Synchronized
try:
    from queue import Queue
except:
    from Queue import Queue
# from multiprocessing.connection import Listener
import socket
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

    q = Queue()

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, _port))

    if isinstance(port, Synchronized):
        port.value = s.getsockname()[1]

    s.listen(1)
    conn, _ = s.accept()

    def get_requests_in_thread():
        while True:
            request = conn.recv(4096).decode("utf-8")
            q.put(request)

    threading.Thread(target=get_requests_in_thread).start()

    def request_sender(request):
        conn.send(request.encode("utf-8"))

    def request_getter():
        # prompt is ready
        request_sender("<ready>")
        request = q.get()
        return request

    rinstance.read_console = create_read_console(request_getter)
    rinstance.write_console_ex = create_write_console_ex(request_sender)

    rinstance.run()
