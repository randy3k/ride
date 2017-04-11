import ctypes


def create_read_console(request_getter):
    def _read_console(p, buf, buflen, add_history):

        request = request_getter()
        text = request
        code = text.encode("utf-8")
        addr = ctypes.addressof(buf.contents)
        c2 = (ctypes.c_char * buflen).from_address(addr)
        nb = min(len(code), buflen-2)
        c2[:nb] = code[:nb]
        c2[nb:(nb+2)] = b'\n\0'

        return 1

    return _read_console


def create_write_console_ex(request_sender):
    def _write_console_ex(buf, buflen, otype):

        output = buf.decode("utf-8")
        # todo: send otype
        request_sender(output)

    return _write_console_ex
