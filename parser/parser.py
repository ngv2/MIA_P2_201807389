import ply.yacc as yacc
from parser.lexer import tokens
from commands.EXECUTE import EXECUTE
from commands.MKDISK import MKDISK
from commands.RMDISK import RMDISK
from commands.FDISK import FDISK
from commands.MOUNT import MOUNT
from commands.MKFS import MKFS
from commands.LOGIN import LOGIN
from commands.LOGOUT import LOGOUT
from commands.MKGRP import MKGRP
from commands.RMGRP import RMGRP
from commands.MKUSR import MKUSR
from commands.RMUSR import RMUSR
from commands.MKFILE import MKFILE
from commands.MKDIR import MKDIR
from commands.REP import REP
from interface.Command import Parameter, ParameterList
from parser.ParseError import ParseError
from console.Console import c_println

def p_cmd(p):
    '''cmd : command'''
    p[0] = p[1]


def p_cmd_params(p):
    '''cmd : command param_list'''
    p[1].set_args(p[2].params)
    p[0] = p[1]


########################################################################################################################
def p_command_execute(p):
    '''command : EXECUTE'''
    p[0] = EXECUTE()


def p_command_mkdisk(p):
    '''command : MKDISK'''
    p[0] = MKDISK()


def p_command_rmdisk(p):
    '''command : RMDISK'''
    p[0] = RMDISK()


def p_command_fdisk(p):
    '''command : FDISK'''
    p[0] = FDISK()


def p_command_mount(p):
    '''command : MOUNT'''
    p[0] = MOUNT()


def p_command_mkfs(p):
    '''command : MKFS'''
    p[0] = MKFS()


def p_command_login(p):
    '''command : LOGIN'''
    p[0] = LOGIN()


def p_command_logout(p):
    '''command : LOGOUT'''
    p[0] = LOGOUT()


def p_command_mkusr(p):
    '''command : MKUSR'''
    p[0] = MKUSR()


def p_command_rmusr(p):
    '''command : RMUSR'''
    p[0] = RMUSR()


def p_command_mkgrp(p):
    '''command : MKGRP'''
    p[0] = MKGRP()


def p_command_rmgrp(p):
    '''command : RMGRP'''
    p[0] = RMGRP()


def p_command_mkfile(p):
    '''command : MKFILE'''
    p[0] = MKFILE()


def p_command_mkdir(p):
    '''command : MKDIR'''
    p[0] = MKDIR()


def p_command_rep(p):
    '''command : REP'''
    p[0] = REP()
########################################################################################################################


def p_param_list(p):
    '''param_list : param'''
    p[0] = ParameterList({p[1].key: p[1].value})


def p_param_list_r(p):
    '''param_list : param_list param'''
    p[1].params[p[2].key] = p[2].value
    p[0] = p[1]


def p_param(p):
    '''param : GUION PALABRA'''
    p[0] = Parameter(str.lower(p[2]), "")


def p_param_v(p):
    '''param : GUION PALABRA IGUAL param_value'''
    p[0] = Parameter(str.lower(p[2]), p[4])


def p_param_value(p):
    '''param_value : PALABRA
                   | STRING
                   | NUMERO
    '''
    p[0] = p[1]


# Error rule for syntax errors
def p_error(p):
    ParseError.error = p or ""
    c_println("Syntax error in input!")
    if p is not None:
        c_println(p)


# Build the parser
main_parser = yacc.yacc()
execute_parser = yacc.yacc()

