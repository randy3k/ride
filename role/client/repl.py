import os

from prompt_toolkit.shortcuts import \
    create_prompt_application, create_eventloop, CommandLineInterface
from prompt_toolkit.token import Token
from prompt_toolkit.buffer import AcceptAction
from prompt_toolkit.interface import AbortAction
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import style_from_dict, DEFAULT_STYLE_EXTENSIONS
from prompt_toolkit.layout.lexers import PygmentsLexer

from pygments.lexers.r import SLexer
from pygments.styles import get_style_by_name

# from . import api
# from . import interface
from .keybindings import create_key_registry
# from .completion import RCompleter


class MultiPrompt(object):
    prompts = {
        "r": "r$> ",
        "help": "help?> ",
        "help_search": "help??> ",
        "debug": "debug%> "
    }
    _prompt_mode = "r"

    @property
    def prompt(self):
        return self.prompts[self._prompt_mode]

    @property
    def mode(self):
        return self._prompt_mode

    @mode.setter
    def mode(self, m):
        self._prompt_mode = m


# def create_r_eventloop():
#     def process_events(context):
#         while True:
#             if context.input_is_ready():
#                 break
#             api.process_events()
#             time.sleep(0.01)
#     eventloop = create_eventloop(inputhook=process_events)

#     # these are necessary to run the completions in main thread.
#     eventloop.run_in_executor = lambda callback: callback()

#     return eventloop


class RCommandlineInterface(CommandLineInterface):

    def abort(self):
        # make sure a new line is print
        self._abort_flag = True
        self._redraw()
        self.output.write("\n")
        self.reset()
        self.renderer.request_absolute_cursor_position()
        self.current_buffer.reset(append_to_history=True)


def create_style():
    style_dict = {}
    style_dict.update(DEFAULT_STYLE_EXTENSIONS)
    style_dict.update(get_style_by_name("default").styles)
    style_dict[Token.RPrompt] = "#ansiblue"
    style_dict[Token.HelpPrompt] = "#ansiyellow"
    style_dict[Token.DebugPrompt] = "#ansired"
    return style_from_dict(style_dict)


def create_r_repl(handle_request):
    multi_prompt = MultiPrompt()

    registry = create_key_registry(multi_prompt)

    def get_prompt_tokens(cli):
        if multi_prompt.mode == "r":
            return [(Token.RPrompt, multi_prompt.prompt)]
        elif multi_prompt.mode.startswith("help"):
            return [(Token.HelpPrompt, multi_prompt.prompt)]
        elif multi_prompt.mode == "debug":
            return [(Token.DebugPrompt, multi_prompt.prompt)]

    history = FileHistory(os.path.join(os.path.expanduser("~"), ".role_history"))

    def accept_action(cli, buf):
        if multi_prompt.mode == "r":
            def _handler():
                code = buf.text.strip("\n").rstrip()
                if code:
                    handle_request(code)
                    cli.current_buffer.cursor_position = len(code)
                    cli.current_buffer.text = code
                    cli.current_buffer.reset(append_to_history=True)
                cli.output.write("\n")

            cli.run_in_terminal(_handler, render_cli_done=True)

    application = create_prompt_application(
        get_prompt_tokens=get_prompt_tokens,
        key_bindings_registry=registry,
        lexer=PygmentsLexer(SLexer),
        style=create_style(),
        # multiline=True,
        history=history,
        # completer=RCompleter(multi_prompt),
        complete_while_typing=True,
        accept_action=AcceptAction(accept_action),
        on_exit=AbortAction.RETURN_NONE)

    # application.on_start = lambda cli: cli.output.write(interface.r_version() + "\n")

    eventloop = create_eventloop()

    return RCommandlineInterface(
        application=application,
        eventloop=eventloop)
