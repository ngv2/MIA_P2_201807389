from parser import lexer, parser
import os

from interface.Command import Command
from console.Console import c_println
from parser.ParseError import ParseError


class EXECUTE(Command):

    def __init__(self):
        self.args = {}
        self.path = ""

    def set_args(self, the_args):
        self.args = the_args

    def parse_args(self):
        for name, value in self.args.items():
            if name == "path":
                self.path = value
                continue
            c_println("EXECUTE->ARGUMENTO INVALIDO ", name)
            return 1

        # Argumentos obligatorios
        if self.path == "":
            c_println("EXECUTE->NO SE BRINDO EL ARGUMENTO PATH")
            return 1
        return 0

    def run_command(self):
        parse_args_result = self.parse_args()
        if parse_args_result != 0:
            return parse_args_result

        # Verificar que el archivo exista
        if not os.path.isfile(self.path):
            c_println(f"EXECUTE->ERROR-> EL ARCHIVO {self.path} NO EXISTE")
            return 3

        file = open(self.path)
        scanner = file.readlines()
        for line in scanner:
            line = line.strip()
            if line == "":
                continue

            c_println(">>>>>", line)
            if line.lstrip()[0] == '#':
                continue
            cmd = self.parse_input(line)
            if ParseError.error is not None:
                c_println(f"Error en el comando.")
                continue
            cmd_return = cmd.run_command()
            c_println("EXEC->Resultado del comando:" + str(cmd_return))
            c_println("###################################################################################")

        file.close()
        return 0

    def parse_input(self, input_s):
        result = parser.execute_parser.parse(input_s, lexer=lexer.execute_lexer)
        # print("Parsed execute command:")
        # print(result)
        return result

