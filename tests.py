#!/usr/bin/env python3

# this file will later be tests for certain classes
# currently functions as testing for certain code

# initial thought: make copy of st to check whether nothing was parsed?
# second thought - measure length and compare (if we want to do this)
# of course, the second item in the tuple is empty if this is the case

from poc import Symbol

import re

def test_create_symbol():
    """
    old test:
        - manual symbol creation
        - manual parsing
    """
    st = "first second third fourth fifth"

    sw = Symbol('\w+')
    ss = Symbol(' ')

    while st:
        st, curr = sw.parse(st)
        print("parsed: {}".format(curr))
        st, space = ss.parse(st)

def test_cfg_manual():
    """
    test:
        - create mapping from cfg expr
        - create aggregate Symbol with arithmetic and parse
    """

    in_cfg = (
        "\G :\WORD \SPACE \G | \\0\n"
        "\WORD :\w+\n"
        "\SPACE : "
    )

    lines = [line for line in in_cfg.split('\n') if line.strip()]
    mappings = Symbol.create_mappings(lines)

    sw = Symbol(mappings['WORD'])
    ss = Symbol(mappings['SPACE'])

    g = sw + ss
    g.rrec()
    #g = g | Symbol('')

    st = "first second third fourth fifth"
    g.parse(st)

test_cfg_manual()

def test_inp_cfg():
    """
    Simple example:
    arg1: CFG that only has two important nonterminals: WORD and SPACE
    arg2: "WORD", meaning "return all parts of input that are WORD tokens"
    """

    # -> space is included if it's part of regex ?
    # here, there is NO SPACE after the colon
    # however, each symbol must be separated by a space
    #   a space in your regex means there must be two spaces ?
    in_cfg = (
        "\G :\WORD \SPACE \G | \\0\n"
        "\WORD :\w+\n"
        "\SPACE : "
    )

    lines = [line.strip() for line in in_cfg.split('\n') if line.strip()]
    mappings = Symbol.create_mappings(lines)

#test_inp_cfg()

def test_time_logs():
    """
    More realistic example?: input formatted as syslog output
    """

    test_st1 = (
        "03:45 - 12 - first message\n"
        "04:45 - 13 - second message\n"
    )

    in_cfg = (
        "\\G :\\T - \\N - \\MSG\n"
        "\\T:\d\d:\d\d\n"
        "\\N:\d\d\n"
        "\\MSG:\w+"
    )
