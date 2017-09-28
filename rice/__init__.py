from __future__ import unicode_literals
import optparse
import os
import sys

from .deps import dependencies_loaded
from .riceapp import RiceApplication

try:
    from setproctitle import setproctitle
except Exception:
    pass

__version__ = '0.0.27-dev'


def main():
    if not dependencies_loaded:
        print("Dependencies not loaded.")
        return

    try:
        setproctitle(" ".join(["rice"] + sys.argv[1:]))
    except Exception:
        pass

    parser = optparse.OptionParser("usage: rice")
    parser.add_option("-v", "--version", action="store_true", dest="version", help="get version")
    parser.add_option("--no-environ", action="store_true", dest="no_environ", help="Don't read the site and user environment files")
    parser.add_option("--no-site-file", action="store_true", dest="no_site_file", help="Don't read the site-wide Rprofile")
    parser.add_option("--no-init-file", action="store_true", dest="no_init_file", help="Don't read the user R profile")
    parser.add_option("--local-history", action="store_true", dest="local_history", help="Force using local history file")
    parser.add_option("--global-history", action="store_true", dest="global_history", help="Force using global history file")
    parser.add_option("--no-history", action="store_true", dest="no_history", help="Don't load any history files")
    parser.add_option("--vanilla", action="store_true", dest="vanilla", help="Combine --no-history --no-environ --no-site-file --no-init-file")

    options, args = parser.parse_args()

    if options.version:
        print("rice version: {}".format(__version__))
        print("python version: {:d}.{:d}.{:d}".format(
            sys.version_info.major,
            sys.version_info.minor,
            sys.version_info.micro))
        print("python executable: {}".format(sys.executable))
        return

    os.environ["RICE_VERSION"] = __version__
    os.environ["RETICULATE_PYTHON"] = sys.executable

    RiceApplication().run(options)
