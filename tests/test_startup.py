from __future__ import unicode_literals


def test_startup(terminal):
    try:
        terminal.line(0).assert_startswith("Python")
    except Exception:
        print("\n".join(terminal.screen.display))
        raise
