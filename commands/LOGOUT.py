import os
from interface.Command import Command
from console.Console import c_println
from general.LoggedUser import LoggedUser


class LOGOUT(Command):

    def __init__(self):
        self.args = {}

    def set_args(self, the_args):
        self.args = the_args

    def parse_args(self):
        if len(self.args.items()) != 0:
            c_println("LOGOUT->ERROR->ESTE COMANDO NO TOMA NINGÚN ARGUMENTO")
            return 1
        return 0

    def run_command(self):
        parse_args_result = self.parse_args()
        if parse_args_result != 0:
            return parse_args_result

        if LoggedUser.username == "":
            c_println("LOGOUT->ERROR->NO SE HA INICIADO SESIÓN")
            return 1

        LoggedUser.username = ""
        LoggedUser.uid = -1
        LoggedUser.gid = -1
        LoggedUser.partition_id = ""

        c_println("LOGOUT->CERRADO DE SESIÓN CON ÉXITO")
