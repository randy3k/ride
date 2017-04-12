from multiprocessing import Process, Value
import time

from .server import server
from .client import client


def run():
    port = Value("i", 0)
    p = Process(target=server.run, kwargs={"port": port})
    p.start()

    while True:
        if port.value != 0:
            break
        time.sleep(0.05)

    client.run(port=port.value)
    p.terminate()
