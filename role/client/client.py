try:
    from queue import Queue
except:
    from Queue import Queue
# from multiprocessing.connection import Client
import socket
import threading
import sys

from .repl import create_r_repl


def debug(*args):
    with open("/tmp/debug", "a") as f:
        f.write(*args)
        f.write("\n")


def run(host='localhost', port=0):
    conn = socket.create_connection((host, port))

    ack = threading.Condition()
    receiveq = Queue()
    sendq = Queue()

    def get_requests_in_thread():
        while True:
            # todo: handle more than 4096 bytes
            request = conn.recv(4096)
            # debug(request.decode("utf-8"))

            if request == b"<server_ack>":
                with ack:
                    ack.notify()
            else:
                # acknowledge
                conn.send(b"<client_ack>")
                receiveq.put(request.decode("utf-8"))

    threading.Thread(target=get_requests_in_thread).start()

    def send_requests_in_thread():
        while True:
            with ack:
                conn.send(sendq.get().encode("utf-8"))
                ack.wait()

    threading.Thread(target=send_requests_in_thread).start()

    ready = threading.Condition()

    def processing_requests():
        while True:
            request = receiveq.get()
            if request == "<ready>":
                with ready:
                    ready.notify()
            else:
                sys.stdout.write(request)

    threading.Thread(target=processing_requests).start()

    def request_sender(request):
        sendq.put(request)
        with ready:
            ready.wait()

    cli = create_r_repl(request_sender)

    cli.run()
