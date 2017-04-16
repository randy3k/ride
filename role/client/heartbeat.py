import zmq
from zmq import ZMQError
import time
from threading import Thread


class HeartBeatChannel(Thread):
    _closed = False
    _beating = True
    _timeout = 1

    def __init__(self, context, port):
        super(HeartBeatChannel, self).__init__()
        self.hb = context.socket(zmq.REQ)
        self.hb.connect("tcp://127.0.0.1:{}".format(port))
        self.hb.setsockopt(zmq.LINGER, 0)

    def run(self):
        while not self._closed:
            try:
                self.hb.send(b"ping")
                request_time = time.time()
                if self.hb.poll(1000 * self._timeout):
                    self._beating = True
                    self.hb.recv()
                    reminder = self._timeout - (time.time() - request_time)
                    if reminder > 0:
                        time.sleep(reminder)
                else:
                    self._beating = False

            except ZMQError:
                self._beating = False
                break

    def is_beating(self):
        return self.is_alive() and not self._closed and self._beating

    def close(self):
        self._closed = True
        self.hb.close()
