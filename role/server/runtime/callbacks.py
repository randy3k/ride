import ctypes


def create_read_console(get_text):
    def _read_console(p, buf, buflen, add_history):
        text = get_text()
        if text is None:
            return 0

        code = text.encode("utf-8")
        addr = ctypes.addressof(buf.contents)
        c2 = (ctypes.c_char * buflen).from_address(addr)
        nb = min(len(code), buflen-2)
        c2[:nb] = code[:nb]
        c2[nb:(nb+2)] = b'\n\0'

        return 1

    return _read_console


def create_write_console_ex(_handler):
    def _write_console_ex(buf, buflen, otype):

        output = buf.decode("utf-8")
        # todo: send otype
        _handler(output)

    return _write_console_ex
