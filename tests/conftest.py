from __future__ import unicode_literals
import pytest
import sys
import time
from .terminal import Terminal


def pytest_addoption(parser):
    parser.addoption(
        "--coverage", action="store_true", default=False, help="generate coverage report"
    )


@pytest.fixture(scope='session')
def radian_command(pytestconfig):
    if pytestconfig.getoption("coverage"):
        radian_command = [sys.executable]
    else:
        radian_command = [sys.executable]

    return radian_command


@pytest.fixture(scope='function')
def terminal(radian_command):
    with Terminal.open(radian_command) as t:
        yield t
