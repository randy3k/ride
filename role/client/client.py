try:
    from queue import Queue
except:
    from Queue import Queue
# from multiprocessing.connection import Client
import socket
import threading
import sys

from .repl import create_r_repl


def run(host='localhost', port=0):
    conn = socket.create_connection((host, port))
    conn.recv(4096)  # ready

    cond = threading.Condition()
    q = Queue()

    def get_requests_in_thread():
        while True:
            request = conn.recv(4096).decode("utf-8")
            q.put(request)

    threading.Thread(target=get_requests_in_thread).start()

    def processing_requests():
        while True:
            request = q.get()
            with cond:
                with open("/tmp/test", "a") as f:
                    f.write(request + "({})".format(request == "<ready>") + "\n")
                if request == "<ready>":
                    cond.notify()
                else:
                    # print output
                    sys.stdout.write(request)

    threading.Thread(target=processing_requests).start()

    def request_sender(request):
        with cond:
            conn.send(request.encode("utf-8"))
            cond.wait()

    cli = create_r_repl(request_sender)

    cli.run()
