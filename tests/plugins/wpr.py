import os
import re
import subprocess
import sys
from itertools import chain, repeat


def pytest_addoption(parser):
    group = parser.getgroup('wpr')
    group.addoption(
        '--use-wpr',
        action='store_true',
    )
    group.addoption(
        '--wpr-path',
        default=None,
    )
    group.addoption(
        '--wpr-output',
        default=None,
    )
    group.addoption(
        '--wpr-profile',
        action='append',
    )


class Plugin(object):
    def __init__(self, config):
        self.config = config

    def pytest_runtest_logstart(self, nodeid, location):
        wpr_path = self.config.getoption('--wpr-path')
        if not wpr_path:
            return
        msg = "{} ({}) - begin".format(nodeid, os.getpid())
        create_mark(wpr_path, msg)

    def pytest_runtest_logfinish(self, nodeid, location):
        wpr_path = self.config.getoption('--wpr-path')
        if not wpr_path:
            return
        msg = "{} ({}) - end".format(nodeid, os.getpid())
        create_mark(wpr_path, msg)


def pytest_configure(config):
    if sys.platform != 'win32':
        return

    if not config.getoption('--use-wpr'):
        return

    config.pluginmanager.register(Plugin(config))

    wpr_path = config.getoption('--wpr-path')
    wpr_profiles = config.getoption('--wpr-profile')

    start_wpr(wpr_path, wpr_profiles)


def pytest_unconfigure(config):
    if sys.platform != 'win32':
        return

    if not config.getoption('--use-wpr'):
        return

    wpr_path = config.getoption('--wpr-path')
    wpr_output = config.getoption('--wpr-output')

    stop_wpr(wpr_path, wpr_output)


_name_re = re.compile(r"(?P<file>.+?)::(?P<name>.+?) \(.*\)$")


def current_test_name():
    try:
        name = os.environ["PYTEST_CURRENT_TEST"]
    except KeyError:
        return "<outside test>"
    m = _name_re.match(name)
    if not m:
        raise RuntimeError(
            "Could not extract test name from {}".format(name)
        )
    return m.group("name")


def start_wpr(executable, profiles):
    # type: (str, List[str]) -> None
    args = [executable]
    args.extend(chain.from_iterable(zip(repeat('-start'), profiles)))
    subprocess.check_call(args)


def stop_wpr(executable, output_path):
    # type: (str, str) -> None
    subprocess.check_call([executable, '-stop', output_path])


def create_mark(executable, message):
    # type: (str, str) -> None
    subprocess.check_call([executable, '-marker', message])
