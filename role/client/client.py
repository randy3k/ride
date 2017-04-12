from multiprocessing import Queue
from multiprocessing.connection import Client
import threading
import sys
import signal

from .repl import create_r_repl


def run(host='localhost', port=0):
    conn = Client((host, port))

    receiveq = Queue()
    sendq = Queue()

    def get_requests_in_thread():
        while True:
            try:
                request = conn.recv()
                receiveq.put(request.decode("utf-8"))
            except (OSError, EOFError):
                break

    threading.Thread(target=get_requests_in_thread).start()

    def send_requests_in_thread():
        while True:
            try:
                conn.send(sendq.get().encode("utf-8"))
            except EOFError:
                break

    threading.Thread(target=send_requests_in_thread).start()

    ready = threading.Condition()

    def processing_requests():
        while True:
            try:
                request = receiveq.get()
            except EOFError:
                break
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

    signal.signal(signal.SIGINT, signal.SIG_IGN)

    cli = create_r_repl(request_sender)
    cli.run()
    sendq.close()
    receiveq.close()
    conn.close()
