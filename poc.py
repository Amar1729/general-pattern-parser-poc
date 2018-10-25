#!/usr/bin/env python3

import copy
import re

# note - what should an error look like?
# if s is returned in entirety and the next symbol doesn't match anything?

# note - how will recursive symbols work? if i do symbol replacement

class ParseError(Exception):
    pass

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
            # TODO - possibly treat 'regex' differently if prefixed with r or not?
            # -> so we can form literals easily?
            self.str = "r'{}'".format(regex)
        else:
            self.str = "\\0"

        if regex:
            self.regex = re.compile(regex)
            self.parse_func = Symbol._create_parse_func(self.regex)
        elif regex == '': # empty regex -> null terminate
            self.parse_func = lambda inp: (inp, True)

        # introduce a Symbol type, to help decide how to combine two symbols
        if kwargs.get('type_'):
            self.type_ = kwargs.get('type_')
        else:
            self.type_ = 'agg'

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
                # if this is the empty-string parser, it should still return True
                return (inp_str[rem_len:], result if result else True)
            return (inp_str, False)
        return func

    def parse(self, inp_str):
        return self.parse_func(inp_str)

    def __repr__(self):
        return self.str

    def __str__(self):
        return self.str

    def __add__(self, other):
        """
        Change the parse function when symbols are added together
        """

        if not isinstance(other, Symbol):
            raise TypeError("cannot add with type: {}".format(type(other)))

        def _f(inp_str):
            inp, ret = self.parse(inp_str)
            print("parsed: {}".format(ret))
            inp, ret = other.parse(inp)
            return inp, ret

        s = Symbol(None)
        s.str = "{} + {}".format(self.str, other.str)
        s.parse_func = _f
        if self.type_ == 'lit' and other.type_ == 'lit':
            s.type_ = 'lit'
        return s

    def __or__(self, other):

        if not isinstance(other, Symbol):
            raise TypeError("cannot or with type: {}".format(type(other)))

        def _f(inp_str):
            if not inp_str:
                return inp_str, ""
            _inp_original = copy.copy(inp_str)
            inp, ret = self.parse(inp_str)
            if _inp_original == inp:
                print("parsed (or): {}".format(ret))
                inp, ret = other.parse(inp_str)
            else:
                print("parsed (first): {}".format(ret))

            return inp, ret

        s = Symbol(None)
        # TODO - add a check on self.regex here to decide whether to incl ()
        s.str = "({}) | ({})".format(self.str, other.str)
        s.parse_func = _f
        if self.type_ == 'lit' and other.type_ == 'lit':
            s.type_ = 'lit'
        return s

    def __ror__(self, other):
        return self.__or__(other)

    # "hardcoded" recursion
    # NOTE - right now, ALL RECURSIVE SYMBOLS have an implicit empty string???

    def lrec(self):
        # lrec doesnt work yet? rrec does
        _parse_func = self.parse_func
        def _f(inp_str):
            if not inp_str:
                return inp_str, ""
            inp, ret = _f(inp_str)
            inp, ret = _parse_func(inp)
            return inp, ret

        self.str = "* ({})".format(self.str)
        self.parse_func = _f
        self.type_ = None

    def rrec(self):
        _parse_func = self.parse_func
        def _f(inp_str):
            if not inp_str:
                return inp_str, ""
            inp, ret = _parse_func(inp_str)
            inp, ret = _f(inp)
            return inp, ret

        self.str = "({}) *".format(self.str)
        self.parse_func = _f
        self.type_ = None

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
