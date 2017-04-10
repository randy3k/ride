import traceback

from . import api
from . import interface


def prase_input_complete(cli):
    return api.parse_vector(api.mk_string(cli.current_buffer.text))[1] != 2


def process_input(cli):
    code = cli.current_buffer.text.strip("\n").rstrip()
    try:
        result = interface.reval(code)
        if result and api.visible():
            # todo: use cli.output.write
            interface.rprint(result)
    except SyntaxError as e:
        print(e)
    except RuntimeError as e:
        pass
    finally:
        cli.current_buffer.cursor_position = len(code)
        cli.current_buffer.text = code
        cli.current_buffer.reset(append_to_history=True)

    cli.output.write("\n")


# def process_input(cli):
#     text = cli.current_buffer.text
#     lines = text.strip("\n").split("\n")
#     lineno = 0
#     status = [True]
#     for i in range(len(lines)):
#         code = "\n".join(lines[lineno:(i+1)]).strip("\n")
#         if api.parse_vector(api.mk_string(code))[1] != 2:
#             lineno = i + 1
#             cli.current_buffer.cursor_position = 0
#             cli.current_buffer.text = code
#             cli.run_in_terminal(lambda: _process_input(cli, status), render_cli_done=True)
#             if not status[0]:
#                 break
#     cli.current_buffer.cursor_position = 0
#     cli.current_buffer.text = "\n".join(lines[lineno:]).strip("\n")


def show_help(cli):
    text = cli.current_buffer.text.strip()
    try:
        if text:
            interface.help(text)
    except SyntaxError as e:
        print(e)
    except RuntimeError as e:
        pass
    finally:
        cli.output.write("\n")


def show_help_search(cli, try_all_packages=False):
    text = cli.current_buffer.text.strip()
    try:
        if text:
            interface.help_search(text)
    except SyntaxError as e:
        print(e)
    except RuntimeError as e:
        pass
    finally:
        cli.output.write("\n")


_globals = {"api": api, "interface": interface}
_locals = {}


def process_python_input(cli):
    text = cli.current_buffer.text
    try:
        try:
            result = eval(text, _globals, _locals)
            if result:
                # todo: use cli.output.write
                print(result)

        except SyntaxError:
            exec(text, _globals, _locals)

    except Exception:
        traceback.print_exc()

    cli.current_buffer.reset(append_to_history=True)

    # print a new line between prompts
    cli.output.write("\n")
