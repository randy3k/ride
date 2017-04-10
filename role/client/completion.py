from prompt_toolkit.completion import Completer, Completion

from . import api
from . import interface


class RCompleter(Completer):

    def __init__(self, multi_prompt):
        self.multi_prompt = multi_prompt
        self.assignLinebuffer = self.get_utils_func(".assignLinebuffer")
        self.assignEnd = self.get_utils_func(".assignEnd")
        self.guessTokenFromLine = self.get_utils_func(".guessTokenFromLine")
        self.completeToken = self.get_utils_func(".completeToken")
        self.retrieveCompletions = self.get_utils_func(".retrieveCompletions")

    def get_utils_func(self, fname):
        f = interface.rlang(api.mk_symbol(":::"), api.mk_string("utils"), api.mk_string(fname))
        api.preserve_object(f)
        return f

    def get_completions(self, document, complete_event):
        completions = []
        token = ""
        if self.multi_prompt.mode in ["r", "help"]:
            text = document.text_before_cursor
            s = api.protect(api.mk_string(text))
            interface.rcall(self.assignLinebuffer, s)
            interface.rcall(self.assignEnd, api.scalar_integer(len(text)))
            token = interface.rcopy(interface.rcall(self.guessTokenFromLine))[0]
            if (len(token) > 3 and text[-1].isalnum()) or complete_event.completion_requested:
                interface.rcall(self.completeToken)
                completions = interface.rcopy(interface.rcall(self.retrieveCompletions))
            api.unprotect(1)
        for c in completions:
            yield Completion(c, -len(token))
