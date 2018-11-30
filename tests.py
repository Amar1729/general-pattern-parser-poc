#!/usr/bin/env python3

# this file will later be tests for certain classes
# currently functions as testing for certain code

# initial thought: make copy of st to check whether nothing was parsed?
# second thought - measure length and compare (if we want to do this)
# of course, the second item in the tuple is empty if this is the case

from poc import Symbol, CFG

import re

def test_star():
    a = Symbol('a*')

    assert a.parse('')[1] == True
    assert a.parse('aa')[0] == ''
    assert a.parse('aa')[1] == 'aa'
    assert a.parse('aab')[0] == 'b'
    assert a.parse('aaba')[0] == 'ba'

def test_add():
    a = Symbol('a')
    b = Symbol('b')
    c = a + b

    assert c.parse('')[1] == False
    assert c.parse('ab')[0] == ''
    assert c.parse('abb')[0] != ''

    a = Symbol('a*')
    b = Symbol('b*')
    c = a + b

    assert c.parse('')[1] == True
    assert c.parse('ab')[0] == ''
    assert c.parse('aab')[0] == ''
    assert c.parse('abb')[0] == ''
    assert c.parse('aa')[0] == ''
    assert c.parse('bb')[0] == ''
    assert c.parse('aba')[0] != ''

def test_or():
    a = Symbol('a')
    b = Symbol('b')
    c = a | b

    assert c.parse('')[1] == False
    assert c.parse('a')[0] == ''
    assert c.parse('b')[0] == ''

    a = Symbol('a*')
    b = Symbol('b*')
    c = a | b

    assert c.parse('')[1] == True
    assert c.parse('aa')[0] == ''
    assert c.parse('aa')[1] == 'aa'
    assert c.parse('aab')[0] == 'b'
    assert c.parse('aaba')[0] == 'ba'
    assert c.parse('bb')[0] == ''
    assert c.parse('bb')[1] == 'bb'
    assert c.parse('bba')[0] == 'a'
    assert c.parse('bbab')[0] == 'ab'

def test_add_or():
    a = Symbol('a')
    b = Symbol('b')
    c = Symbol('c')

    d = (a+b)|c

    assert d.parse('')[1] == False
    assert d.parse('ab')[0] == ''
    assert d.parse('c')[0] == ''

    d = a+(b|c)

    assert d.parse('')[1] == False
    assert d.parse('ab') == ('', 'b')
    assert d.parse('ac') == ('', 'c')

def test_rec():
    d = {'a':Symbol(None)}
    _a = (Symbol('a') + d['a']) | Symbol('')
    d['a'].update(_a)

    assert d['a'].parse('') == ('', True)
    assert d['a'].parse('a') == ('', True)
    assert d['a'].parse('aa') == ('', True)

    d = {'g': Symbol(None)}
    _g = (Symbol('a') + d['g'] + Symbol('b')) | Symbol('')
    d['g'].update(_g)

    assert d['g'].parse('') == ('', True)
    assert d['g'].parse('ab') == ('', 'b')
    assert d['g'].parse('aabb') == ('', 'b')
    assert d['g'].parse('aaabb') == ('', False)
    assert d['g'].parse('aabbb') == ('b', 'b')

def test_read_expr():
    expr = "\\A:a"
    cfg = CFG(expr)

    assert cfg.root == 'A'
    assert cfg.parse('')[1] == False
    assert cfg.parse('a')[0] == ''
    assert cfg.parse('aa') == ('a', 'a')

    expr = "\\A:a + \\B\n\\B:b*"
    cfg = CFG(expr)

    assert cfg.root == 'A'
    assert cfg.parse('')[1] == False
    assert cfg.parse('a')[0] == ''
    assert cfg.parse('ab')[0] == ''
    assert cfg.parse('abb')[0] == ''
    assert cfg.parse('abba') == ('a', 'bb')

test_star()
test_add()
test_or()
test_add_or()
test_rec()

test_read_expr()

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
