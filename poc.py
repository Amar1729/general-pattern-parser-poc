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
        # regex:
        # None -> empty regex that can be updated (does this matter?)
        # '' -> literally nothing
        # nonempty string -> a regex for that
        if regex:
            # TODO - possibly treat 'regex' differently if prefixed with r or not?
            # -> so we can form literals easily?
            self.str = "r'{}'".format(regex)
        else:
            self.str = "\\0"

        if regex:
            self.raw = regex
            self.regex = re.compile(regex)
            self.parse_func = Symbol._create_parse_func(self.regex)
        elif regex == '': # empty regex -> null terminate
            self.raw = ''
            self.parse_func = lambda inp: (inp, True)

        # introduce a Symbol type, to help decide how to combine two symbols
        if kwargs.get('type_'):
            self.type_ = kwargs.get('type_')
        else:
            self.type_ = 'agg'

        # enabled for output?
        #self.enabled = True

        # note - how to handle multiline regex?

    def update(self, other):

        if not isinstance(other, Symbol):
            raise TypeError("Cannot update with type {}".format(type(other)))

        self.str = other.str
        try:
            if not other.regex:
                self.regex = other.regex
        except AttributeError:
            pass
        try:
            self.raw = other.raw
        except AttributeError:
            pass
        try:
            self.parse_func = other.parse_func
        except AttributeError:
            # TODO - slightly obtuse error msg
            raise TypeError("Original symbol requires a parse function")
        self.type_ = other.type_

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
            if not ret:
                return inp, ret
            inp, ret = other.parse(inp)
            return inp, ret

        if self.type_ == 'lit' and other.type_ == 'lit':
            return Symbol(self.raw+other.raw, type_='lit')

        s = Symbol(None)
        s.str = "{} + {}".format(self.str, other.str)
        s.parse_func = _f
        return s

    def __or__(self, other):

        if not isinstance(other, Symbol):
            raise TypeError("cannot or with type: {}".format(type(other)))

        def _f(inp_str):
            # note - should there be an empty check+ret here?
            #if not inp_str:
            #    return inp_str, ""
            _inp_original = copy.copy(inp_str)
            inp, ret = self.parse(inp_str)
            if _inp_original == inp:
                inp, ret = other.parse(inp_str)

            return inp, ret

        if self.type_ == 'lit' and other.type_ == 'lit':
            # not totally comfortable about this
            return Symbol(self.raw+'|'+other.raw, type_='lit')

        s = Symbol(None)
        # TODO - add a check on self.regex here to decide whether to incl ()
        s.str = "({}) | ({})".format(self.str, other.str)
        s.parse_func = _f
        return s

    def __ror__(self, other):
        return self.__or__(other)


class CFG():
    """
    Collection of symbols to parse out as a group
    """

    # notes on class vars:
    # self.mappings:
    # { symbol_name : raw_symbol_line }
    #
    # self.symbols:
    # { symbol_name : Symbol() } # condensed symbol. should be able to immediately parse()

    def __init__(self, _cfg):
        # note : include newline chars if they're the only thing in the string?
        lines = _cfg.split('\n')

        # by default, the first symbol will be the start point
        self.root = lines[0][:lines[0].index(':')].strip().lstrip('\\')

        self.__create_mappings(lines)
        self.__create_cfg()

    def __str__(self):
        return '\n'.join(["{}: {}".format(s, e) for s, e in self.symbols.items()])

    def __create_mappings(self, lines):
        """
        extract symbol names and expressions into a dictionary
        """
        def _sym(inp):
            return inp[:inp.index(':')].strip().lstrip('\\')

        def _expr(inp):
            return re.sub(r'.*?:', '', inp, 1)

        self.mappings = {_sym(line):_expr(line) for line in lines}

    def __create_cfg(self):
        """
        From mappings, create the collection of Symbols that form this CFG
        """

        # idea:
        # convert each line to a list of symbols to be combined in one loop
        #   (so that every symbol resolves to something)
        # then loop through again to perform Symbol arithmetic
        #self.symbols = {k:self.__expand_symbol(v) for k, v in self.mappings.items()}
        self.symbols = {k:Symbol('') for k, v in self.mappings.items()}
        for k, v in self.mappings.items():
            _k = self.__expand_symbol(v)
            self.symbols[k].update(_k)

    @staticmethod
    def __split(line):
        """
        Custom split to preserve multiple (2) consecutive spaces
        May be important for regexes including a literal space
        """

        i = 0
        _str = ''

        while i < len(line):
            _str += line[i]
            i += 1

            # return last word in string, or split on spaces
            if i >= len(line) or line[i] == ' ':

                # if there are two consecutive spaces, add a space to the current and next item
                try:
                    if line[i+1] == ' ':
                        _str += ' '
                except IndexError:
                    pass
                yield _str
                i += 1
                _str = ''

    def __is_symbol(self, _str):
        return True if _str.strip().lstrip('\\') in self.mappings else False

    def __expand_symbol(self, line):
        """
        Convert a line with Symbol names to a Symbol
        """

        # TODO - maybe put ParseError handling/raising here, for more modular code?
        try:
            return self.__condense(CFG.__line_to_postfix(line))
        except re.error:
            # TODO - this doesn't actually supress output from re.error
            raise ParseError("Unmatched '(' or ')'")

    @staticmethod
    def __line_to_postfix(line):
        """
        Convert the symbol line to postfix for easier parsing
        """

        stack = []
        output = []

        last_token_sym = False

        def handle_op(op):
            while stack:
                if stack[-1].strip() in '(':
                    break
                else:
                    output.append(stack.pop())
            stack.append(op)

        for token in CFG.__split(line):
            if token.strip() in '+|':
                handle_op(token.strip())
                last_token_sym = False
            elif token.strip() == '(':
                stack.append(token.strip())
                last_token_sym = False
            elif token.strip() == ')':
                if '(' not in stack:
                    raise ParseError("Unmatched ')'")

                while stack:
                    op = stack.pop()
                    if op == '(':
                        break
                    output.append(op)
                last_token_sym = False
            else:
                # literal, regex, or symbol name
                # note that consecutive regexes/literals added together need to be handled properly
                # also note that greedy stuff might fuck up add/or

                if last_token_sym:
                    handle_op('+')
                output.append(token)
                last_token_sym = True

        if '(' in stack:
            raise ParseError("Unmatched '('")

        while stack:
            output.append(stack.pop())

        return output

    def __condense(self, tokens):
        """
        Condense the postfix list of tokens into a single Symbol
        """

        stack = []
        #for token in tokens[::-1]:
        for token in tokens:
            if token == '+':
                try:
                    op_r = stack.pop()
                    op_l = stack.pop()
                except IndexError:
                    raise ParseError("Incorrect expression (too many operators)")
                res = op_l + op_r
                stack.append(res)
            elif token == '|':
                try:
                    op_r = stack.pop()
                    op_l = stack.pop()
                except IndexError:
                    raise ParseError("Incorrect expression (too many operators)")
                res = op_l | op_r
                stack.append(res)
            else:
                # token is a str literal, regex, or SYMBOL_NAME
                sym_name = token.strip().lstrip('\\')
                if sym_name in self.mappings:
                    # TODO - this line right here needs some work
                    # how to properly do symbol expansion and formation?
                    # needs to rely on .parse_func being set() later on (i think?)
                    # note that this is NOT a literal symbol
                    # TODO this isn't correct - shouldn't be Symbolizing this string
                    # -> the string is just the expr of the symbol
                    # -> does not work for recursive symbol names!
                    # -> and probably not for more complex symbols
                    #stack.append(Symbol(self.mappings[sym_name]))
                    #stack.append(self.mappings[sym_name])
                    stack.append(self.symbols[sym_name])
                else:
                    # literal Symbols can be easily recombined later
                    try:
                        stack.append(Symbol(token, type_='lit'))
                    except re.error:
                        raise ParseError("Unmatched '(' or ')'")

        if len(stack) > 1:
            # TODO - better error here, this is too obscure
            raise ParseError("Too many operands")

        return stack.pop()

    def parse(self, inp_str):
        return self.symbols[self.root].parse(inp_str)
