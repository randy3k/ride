from __future__ import unicode_literals
import sys
from .conftest import Terminal


def test_version(pytestconfig):
    if pytestconfig.getoption("coverage"):
        command = [sys.executable, "-m", "coverage", "run", "-m", "radian", "--version"]
    else:
        command = [sys.executable, "-m", "radian", "--version"]
    with Terminal.open(command) as terminal:
        terminal.line(0).assert_startswith("radian version: ")
        import radian
        terminal.line(0).strip().assert_endswith(radian.__version__)
