import ply.lex as lex
import re
from parser.ParseError import ParseError
from console.Console import c_println
tokens = (
    'COMMENT',
    'EXECUTE',
    'MKDISK',
    'RMDISK',
    'FDISK',
    'MOUNT',
    'MKFS',
    'LOGIN',
    'LOGOUT',
    'MKGRP',
    'RMGRP',
    'MKUSR',
    'RMUSR',
    'MKFILE',
    'MKDIR',
    'REP',


    'PALABRA',
    'STRING',
    'NUMERO',
    'GUION',
    'IGUAL'
)


def t_EXECUTE(t):
    r'^EXECUTE'
    return t


def t_MKDISK(t):
    r'^MKDISK'
    return t


def t_RMDISK(t):
    r'^RMDISK'
    return t


def t_FDISK(t):
    r'^FDISK'
    return t


def t_MOUNT(t):
    r'^MOUNT'
    return t


def t_MKFS(t):
    r'^MKFS'
    return t


def t_LOGIN(t):
    r'^LOGIN'
    return t


def t_LOGOUT(t):
    r'^LOGOUT'
    return t


def t_MKGRP(t):
    r'^MKGRP'
    return t


def t_RMGRP(t):
    r'^RMGRP'
    return t


def t_MKUSR(t):
    r'^MKUSR'
    return t


def t_RMUSR(t):
    r'^RMUSR'
    return t


def t_MKDIR(t):
    r'^MKDIR'
    return t


def t_MKFILE(t):
    r'^MKFILE'
    return t


def t_REP(t):
    r'^REP'
    return t


def t_PALABRA(t):
    r'[a-zA-Z_\/.0-9][a-zA-Z_0-9\/.]*'
    return t


def t_STRING(t):
    r'"[^"]*"'
    t.value = t.value[1:-1]
    return t


def t_NUMERO(t):
    r'-?[0-9]+("."[0-9]+)?'
    return t


def t_GUION(t):
    r'-'
    return t


def t_IGUAL(t):
    r'='
    return t


def t_COMMENT(t):
    r'\#.*'
    pass


t_ignore = ' \t'


def t_error(t):
    ParseError.error = f"Illegal character '{t.value[0]}'"
    c_println(ParseError.error)
    t.lexer.skip(1)


lexer = lex.lex(reflags=re.IGNORECASE)
execute_lexer = lex.lex(reflags=re.IGNORECASE)
