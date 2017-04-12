from __future__ import unicode_literals
import re

from prompt_toolkit.key_binding.defaults import load_key_bindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.filters import Condition, HasFocus
from prompt_toolkit.enums import DEFAULT_BUFFER, SEARCH_BUFFER

# from .process_input import process_input, process_python_input, prase_input_complete, \
#     show_help, show_help_search


def create_key_registry(multi_prompt):
    registry = load_key_bindings(
        enable_abort_and_exit_bindings=True,
        enable_system_bindings=True,
        enable_search=True)
    # todo: configurable
    tabsize = 4

    is_begining_of_buffer = Condition(lambda cli: cli.current_buffer.cursor_position == 0)
    is_end_of_buffer = Condition(lambda cli: cli.current_buffer.cursor_position == len(cli.current_buffer.text))
    is_empty = Condition(lambda cli: len(cli.current_buffer.text) == 0)
    is_default_buffer = Condition(lambda cli: cli.current_buffer_name == DEFAULT_BUFFER)
    last_history = Condition(lambda cli: cli.current_buffer.working_index == len(cli.current_buffer._working_lines)-1)
    is_tabble = Condition(lambda cli:  re.search(r"(\n|\s{%d})$" % tabsize, cli.current_buffer.document.text_before_cursor) is not None)

    last_working_index = [-1]

    # prase_complete = Condition(prase_input_complete)

    def in_prompt_mode(m):
        return Condition(lambda _: multi_prompt.mode == m)

    # R prompt

    # @registry.add_binding(Keys.ControlJ, filter=is_default_buffer & in_prompt_mode("r") & prase_complete)
    # @registry.add_binding(Keys.Escape, Keys.ControlJ, filter=is_default_buffer & in_prompt_mode("r"))
    # def _(event):
    #     last_working_index[0] = event.cli.current_buffer.working_index
    #     event.cli.run_in_terminal(lambda: process_input(event.cli), render_cli_done=True)

    @registry.add_binding(Keys.ControlI, filter=is_default_buffer & in_prompt_mode("r") & is_tabble)
    def _(event):
        event.current_buffer.insert_text(" " * tabsize)

    @registry.add_binding("?", filter=is_default_buffer & in_prompt_mode("r") & is_begining_of_buffer)
    def _(event):
        multi_prompt.mode = "help"

    # @registry.add_binding(Keys.ControlY, filter=is_default_buffer & in_prompt_mode("r"))
    # def _(event):
    #     multi_prompt.mode = "debug"

    # @registry.add_binding(Keys.BracketedPaste, filter=is_default_buffer & in_prompt_mode("r"))
    # def _(event):
    #     data = event.data
    #     data = data.replace('\r\n', '\n')
    #     data = data.replace('\r', '\n')
    #     shouldeval = data[-1] == "\n" and len(event.cli.current_buffer.document.text_after_cursor) == 0
    #     if shouldeval:
    #         data = data.strip("\n")
    #         event.current_buffer.insert_text(data)
    #         event.cli.run_in_terminal(lambda: process_input(event.cli), render_cli_done=True)
    #     else:
    #         event.current_buffer.insert_text(data)

    # help prompt

    @registry.add_binding("?", filter=is_default_buffer & in_prompt_mode("help") & is_begining_of_buffer)
    def _(event):
        multi_prompt.mode = "help_search"

    @registry.add_binding(Keys.Backspace, filter=is_default_buffer & in_prompt_mode("help_search") & is_begining_of_buffer)
    @registry.add_binding(Keys.Backspace, filter=is_default_buffer & in_prompt_mode("help") & is_begining_of_buffer)
    @registry.add_binding(Keys.ControlH, filter=is_default_buffer & in_prompt_mode("help_search") & is_begining_of_buffer)
    @registry.add_binding(Keys.ControlH, filter=is_default_buffer & in_prompt_mode("help") & is_begining_of_buffer)
    def _(event):
        multi_prompt.mode = "r"

    # @registry.add_binding(Keys.ControlJ, filter=is_default_buffer & in_prompt_mode("help"))
    # def _(event):
    #     event.cli.run_in_terminal(lambda: show_help(event.cli), render_cli_done=True)
    #     event.cli.current_buffer.reset()
    #     multi_prompt.mode = "r"

    # @registry.add_binding(Keys.ControlJ, filter=is_default_buffer & in_prompt_mode("help_search"))
    # def _(event):
    #     event.cli.run_in_terminal(lambda: show_help_search(event.cli), render_cli_done=True)
    #     event.cli.current_buffer.reset()
    #     multi_prompt.mode = "r"

    @registry.add_binding(Keys.ControlC, filter=is_default_buffer & in_prompt_mode("help"))
    @registry.add_binding(Keys.ControlC, filter=is_default_buffer & in_prompt_mode("help_search"))
    def _(event):
        multi_prompt.mode = "r"

    # debug prompt

    # @registry.add_binding(Keys.ControlY, filter=is_default_buffer & in_prompt_mode("debug"))
    # def _(event):
    #     multi_prompt.mode = "r"

    # @registry.add_binding(Keys.ControlJ, filter=is_default_buffer & in_prompt_mode("debug"))
    # def _(event):
    #     event.cli.run_in_terminal(lambda: process_python_input(event.cli), render_cli_done=True)

    # search promot

    @registry.add_binding(Keys.Escape, filter=HasFocus(SEARCH_BUFFER), eager=True)
    def _(event):
        search_buffer = event.cli.buffers[SEARCH_BUFFER]
        search_buffer.reset()
        event.cli.pop_focus()

    # history

    @registry.add_binding(Keys.Up, filter=is_end_of_buffer & ~last_history)
    def _(event):
        event.current_buffer.history_backward(count=event.arg)
        event.cli.current_buffer.cursor_position = len(event.cli.current_buffer.text)

    @registry.add_binding(Keys.Down, filter=is_end_of_buffer & ~last_history)
    def _(event):
        event.current_buffer.history_forward(count=event.arg)
        event.cli.current_buffer.cursor_position = len(event.cli.current_buffer.text)

    @registry.add_binding(Keys.Down, filter=is_default_buffer & in_prompt_mode("r") & is_empty & last_history)
    def _(event):
        if last_working_index[0] >= 0:
            event.cli.current_buffer.go_to_history(last_working_index[0] + 1)
            last_working_index[0] = -1

    return registry
