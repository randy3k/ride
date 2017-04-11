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


def debug(*args):
    with open("/tmp/debug", "a") as f:
        f.write(*args)
        f.write("\n")


def run(host='localhost', port=0):
    rinstance = Rinstance()
    api.rinstance = rinstance
    if isinstance(port, Synchronized):
        _port = port.value
    else:
        _port = port

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, _port))

    if isinstance(port, Synchronized):
        port.value = s.getsockname()[1]

    s.listen(1)
    conn, _ = s.accept()

    ack = threading.Condition()
    receiveq = Queue()
    sendq = Queue()

    def get_requests_in_thread():
        while True:
            # todo: handle more than 4096 bytes
            request = conn.recv(4096)

            if request == b"<client_ack>":
                with ack:
                    ack.notify()
            else:
                # acknowledge
                conn.send(b"<server_ack>")
                receiveq.put(request.decode("utf-8"))

    threading.Thread(target=get_requests_in_thread).start()

    def send_requests_in_thread():
        while True:
            with ack:
                conn.send(sendq.get().encode("utf-8"))
                ack.wait()

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
