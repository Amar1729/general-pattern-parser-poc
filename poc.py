#!/usr/bin/env python3

import re

# note - what should an error look like?
# if s is returned in entirety and the next symbol doesn't match anything?

# note - how will recursive symbols work? if i do symbol replacement

class Symbol():
    """
    Create a symbol from a regex.
    A 'symbol' is a function that will parse input text according to reg.
    """

    # note -
    # (idea) a symbol may be instantiated with NO REGEX pattern
    # if this is the case, that symbol is a nonterminal (probably recursive)
    # which will be manually created later
    def __init__(self, regex, **kwargs):
        if regex:
            self.regex = re.compile(regex)
            self.parse_func = Symbol._create_parse_func(self.regex)
        elif regex == '': # empty regex -> null terminate
            self.parse_func = lambda inp: (inp, "")

        # enabled for output?
        #self.enabled = True

        # note - how to handle multiline regex?

    @staticmethod
    def _create_parse_func(reg):
        def func(inp_str):
            result = re.match(reg, inp_str)
            if result:
                result = result.group()
                rem_len = len(result)
                return (inp_str[rem_len:], result)
            return (inp_str, "")
        return func

    def parse(self, inp_str):
        return self.parse_func(inp_str)

    # this should maybe in a later Line class
    @staticmethod
    def _sym(inp):
        """
        separate symbol names and expressions
        """
        return inp[:inp.index(':')].strip()[1:]

    @staticmethod
    def _expr(inp):
        return re.sub(r'.*?:', '', inp, 1)

    @staticmethod
    def create_mappings(lines):
        return {Symbol._sym(line):Symbol._expr(line) for line in lines}
