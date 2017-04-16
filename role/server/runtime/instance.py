import os
import subprocess
import sys
from ctypes import c_char, c_char_p, c_int, c_void_p, cast, addressof, CDLL, CFUNCTYPE, POINTER
from .util import ccall, cglobal


class Rinstance(object):
    libR = None
    offset = None
    write_console_ex = None
    read_console = None
    polled_events = None
    clean_up = None

    def __init__(self):
        if 'R_HOME' not in os.environ:
            Rhome = subprocess.check_output(["R", "RHOME"]).decode("utf-8").strip()
            os.environ['R_HOME'] = Rhome
        else:
            Rhome = os.environ['R_HOME']
        os.environ["R_DOC_DIR"] = os.path.join(Rhome, "doc")
        os.environ["R_INCLUDE_DIR"] = os.path.join(Rhome, "include")
        os.environ["R_SHARE_DIR"] = os.path.join(Rhome, "share")
        if sys.platform == "win32":
            libR_path = os.path.join(Rhome, "bin", ['i386', 'x64'][sys.maxsize > 2**32], "R.dll")
        elif sys.platform == "darwin":
            libR_path = os.path.join(Rhome, "lib", "libR.dylib")
        elif sys.platform.startswith("linux"):
            libR_path = os.path.join(Rhome, "lib", "libR.so")

        if not os.path.exists(libR_path):
            raise RuntimeError("Cannot locate R share library.")

        self.libR = CDLL(libR_path)

        cglobal("R_running_as_main_program", self.libR, c_int).value = 1

        _argv = ["role", "--no-save", "--quiet"]
        argn = len(_argv)
        argv = (c_char_p * argn)()
        for i, a in enumerate(_argv):
            argv[i] = c_char_p(a.encode('utf-8'))

        self.libR.Rf_initialize_R(argn, argv)

    def run(self):

        if sys.platform == "win32":
            self._setup_callbacks_win32()
        else:
            self._setup_callbacks_unix()

        self.libR.Rf_mainloop()

    def post_setup(self):
        s = ccall("Rf_ScalarInteger", self.libR, c_void_p, [c_int], 0)
        self.offset = ccall("INTEGER", self.libR, c_void_p, [c_void_p], s).value - s.value

    def _setup_callbacks_win32(self):
        pass

    def _setup_callbacks_unix(self):
        if self.read_console:
            # make sure it is not gc'ed
            self.ptr_read_console = CFUNCTYPE(c_int, c_char_p, POINTER(c_char), c_int, c_int)(
                self.read_console)
            ptr = c_void_p.in_dll(self.libR, 'ptr_R_ReadConsole')
            ptr.value = cast(self.ptr_read_console, c_void_p).value

        if self.write_console_ex:
            c_void_p.in_dll(self.libR, 'ptr_R_WriteConsole').value = 0
            # make sure it is not gc'ed
            self.ptr_write_console_ex = CFUNCTYPE(None, c_char_p, c_int, c_int)(
                self.write_console_ex)
            ptr = c_void_p.in_dll(self.libR, 'ptr_R_WriteConsoleEx')
            ptr.value = cast(self.ptr_write_console_ex, c_void_p).value

        if self.polled_events:
            self.ptr_polled_events = CFUNCTYPE(None)(self.polled_events)
            ptr = c_void_p.in_dll(self.libR, 'R_PolledEvents')
            ptr.value = cast(self.ptr_polled_events, c_void_p).value

        if self.clean_up:
            ptr = c_void_p.in_dll(self.libR, 'ptr_R_CleanUp')
            R_CleanUp_Type = CFUNCTYPE(None, c_int, c_int, c_int)
            old_ptr_clean_up = ptr.value

            def _handler(save_type, status, runlast):
                self.clean_up()
                R_CleanUp_Type(old_ptr_clean_up)(save_type, status, runlast)

            self.ptr_r_clean_up = R_CleanUp_Type(_handler)
            ptr.value = cast(self.ptr_r_clean_up, c_void_p).value
