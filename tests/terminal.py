from __future__ import unicode_literals
import sys
import pyte
import operator
import threading
from contextlib import contextmanager
import six
import time

if sys.platform.startswith("win"):
    import winpty
else:
    import ptyprocess


__all__ = ["PtyProcess", "Screen", "ByteStream", "Terminal", "LazyTerminal"]


if sys.platform.startswith("win"):
    ParentPtyProcess = winpty.PtyProcess
else:
    ParentPtyProcess = ptyprocess.PtyProcess


class PtyProcess(ParentPtyProcess):

    def read(self, nbytes):
        if sys.platform.startswith("win"):
            return super(PtyProcess, self).read(nbytes).encode("utf-8")
        else:
            return super(PtyProcess, self).read(nbytes)

    def write(self, data):
        if sys.platform.startswith("win"):
            super(PtyProcess, self).write(data.decode("utf-8"))
        else:
            super(PtyProcess, self).write(data)


class Screen(pyte.Screen):

    def __init__(self, process, *args, **kwargs):
        self._process = process
        super(Screen, self).__init__(*args, **kwargs)

    def write_process_input(self, data):
        self._process.write(data.encode("utf-8"))


class ByteStream(pyte.ByteStream):

    def start_feeding(self):
        screen = self.listener
        process = screen._process

        def reader():
            while True:
                try:
                    data = process.read(1024)
                    print("\n")
                    print("got some data", data)
                    print("\n")
                except EOFError:
                    break
                if data:
                    self.feed(data)
        t = threading.Thread(target=reader)
        t.start()


class Var(object):
    def __init__(self, getter):
        self.getter = getter

    def __getattr__(self, name):
        # fallback methods
        def _(*args, **kwargs):
            return Var(lambda: getattr(self.getter(), name)(*args, **kwargs))
        return _

    def observe(self, *args, **kwargs):
        return self.getter(*args, **kwargs)

    def _assert(self, op, operand, timeout=5):
        t = time.time()
        while time.time() - t < timeout:
            value = self.getter()
            if op(value, operand):
                break
            time.sleep(0.05)
        else:
            raise Exception("value is {}".format(value))

    def assert_startswith(self, operand, timeout=5):
        self._assert(six.text_type.startswith, operand, timeout)

    def assert_endswith(self, operand, timeout=5):
        self._assert(six.text_type.endswith, operand, timeout)

    def assert_equal(self, operand, timeout=5):
        self._assert(operator.eq, operand, timeout)

    def assert_contains(self, operand, timeout=5):
        self._assert(operator.contains, operand, timeout)


class Terminal(object):

    def __init__(self, process, screen, stream):
        self.process = process
        self.screen = screen
        self.stream = stream

    @classmethod
    @contextmanager
    def open(cls, cmd):
        process = PtyProcess.spawn(cmd)
        screen = Screen(process, 80, 24)
        stream = ByteStream(screen)
        stream.start_feeding()
        try:
            yield cls(process, screen, stream)
        finally:
            process.terminate(force=True)

    def sendintr(self):
        self.process.sendintr()

    def isalive(self):
        return self.process.isalive()

    def write(self, x):
        self.process.write(x.encode('utf-8'))

    def _line(self, num=0):
        # parent's `line` method
        return self.screen.display[num]

    def line(self, num=0):
        return Var(lambda: self._line(num))

    def cursor(self):
        return Var(lambda: (self.screen.cursor.x, self.screen.cursor.y))

    def current_line(self):
        return Var(lambda: self._line(self.screen.cursor.y))

    def previous_line(self, num=1):
        return Var(lambda: self._line(self.screen.cursor.y - num))
