from __future__ import unicode_literals
import sys
import os
import time

from .instance import Rinstance
from . import interface
from . import api
from . import util
from .callbacks import create_read_console, create_write_console_ex
from prompt_toolkit import Prompt
from prompt_toolkit.eventloop import create_event_loop, set_event_loop

from prompt_toolkit.utils import is_windows
from prompt_toolkit.layout.lexers import PygmentsLexer
from pygments.lexers.r import SLexer
from prompt_toolkit.styles import default_style, merge_styles, style_from_pygments
from pygments.styles import get_style_by_name
from prompt_toolkit.history import FileHistory
from prompt_toolkit.layout.processors import HighlightMatchingBracketProcessor

from prompt_toolkit.enums import EditingMode
from prompt_toolkit.formatted_text import ANSI

from .completion import RCompleter
from .keybinding import create_keybindings


def rice_settings():
    settings = {
        "color_scheme": interface.get_option("rice.color_scheme", "native"),
        "editing_mode": interface.get_option("rice.editing_mode", "emacs"),
        "show_statusbar": interface.get_option("rice.show_statusbar", 1) == 1,
    }
    return settings


class MultiPrompt(Prompt):
    _prompts = {
        "r": ANSI("\x1b[34mr$>\x1b[0m "),
        "help": ANSI("\x1b[33mhelp?>\x1b[0m "),
        "help_search": ANSI("\x1b[33mhelp??>\x1b[0m "),
        "debug": "debug%> "
    }
    _default_prompt_mode = "r"

    def __init__(self, *args, **kwargs):
        super(MultiPrompt, self).__init__(*args, **kwargs)
        self.style = None
        self.app.prompt_mode = self._default_prompt_mode

    def _bottom_toolbar(self):
        path = interface.rcopy(interface.reval("base::getwd()"), simplify=True)
        return util.pretty_path(path)

    def prompt(self, message=None, color_scheme="vim", mode="emacs", show_statusbar=True, **kwargs):
        if not message:
            message = self._prompts[self.app.prompt_mode]

        editing_mode = EditingMode.VI if mode == "vi" or mode == "vim" else EditingMode.EMACS
        if not self.style:
            self.style = merge_styles([
                default_style(),
                style_from_pygments(get_style_by_name(color_scheme))])

        return super(MultiPrompt, self).prompt(
            message,
            editing_mode=editing_mode,
            style=self.style,
            bottom_toolbar=self._bottom_toolbar if show_statusbar else None,
            **kwargs)


if not is_windows():
    from prompt_toolkit.input.vt100 import Vt100Input

    class CustomVt100Input(Vt100Input):
        @property
        def responds_to_cpr(self):
            return False


def printer(text, otype=0):
    if otype == 0:
        sys.stdout.write(text)
    else:
        sys.stderr.write(text)


def create_multi_prompt():

    history = FileHistory(os.path.join(os.path.expanduser("~"), ".rice_history"))
    if not is_windows():
        vt100 = CustomVt100Input(sys.stdin)

    def process_events(context):
        while True:
            if context.input_is_ready():
                break
            api.process_events()
            time.sleep(1.0 / 30)

    set_event_loop(create_event_loop(inputhook=process_events))

    rcompleter = RCompleter()

    mp = MultiPrompt(
        multiline=True,
        complete_while_typing=True,
        enable_suspend=True,
        lexer=PygmentsLexer(SLexer),
        completer=rcompleter,
        history=history,
        extra_key_bindings=create_keybindings(),
        extra_input_processor=HighlightMatchingBracketProcessor(),
        input=vt100 if not is_windows() else None
    )

    def on_render(app):
        if app.is_aborting:
            printer("\n")

    mp.app.on_render += on_render

    return mp


def clean_up(save_type, status, runlast):
    pass


def show_message(buf):
    printer(buf.decode("utf-8"))


class RiceApplication(object):

    def run(self):
        mp = create_multi_prompt()

        rinstance = Rinstance()

        _first_time = [True]
        _settings = [None]

        def result_from_prompt(p):
            if _first_time[0]:
                _settings[0] = rice_settings()
                printer(interface.r_version(), 0)
                _first_time[0] = False

            printer("\n")
            text = None
            while text is None:
                try:
                    if p == "> ":
                        text = mp.prompt(
                            color_scheme=_settings[0].get("color_scheme"),
                            mode=_settings[0].get("editing_mode"),
                            show_statusbar=_settings[0].get("show_statusbar"))
                    else:
                        # invoked by `readline`
                        text = mp.prompt(
                            message=p + " ",
                            mode=_settings[0].get("editing_mode"),
                            multiline=False,
                            lexer=None,
                            completer=None,
                            history=None,
                            extra_key_bindings=None)
                except Exception as e:
                    if isinstance(e, EOFError):
                        # todo: confirmation
                        return None
                    else:
                        raise e
                except KeyboardInterrupt:
                    pass

            return text

        rinstance.read_console = create_read_console(result_from_prompt)
        rinstance.write_console_ex = create_write_console_ex(printer)
        rinstance.clean_up = clean_up
        rinstance.show_message = show_message

        # to make api work
        api.rinstance = rinstance

        rinstance.run()
