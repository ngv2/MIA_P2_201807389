import os
from interface.Command import Command
from console.Console import c_println


class RMDISK(Command):
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
            c_println("RMDISK->ARGUMENTO INVALIDO ", name)
            return 1

        if self.path == "":
            c_println("RMDISK->NO SE BRINDO EL ARGUMENTO PATH")
            return 1
        return 0

    def run_command(self):
        parse_args_result = self.parse_args()
        if parse_args_result != 0:
            return parse_args_result

        if not os.path.isfile(self.path):
            c_println(f"RMDISK->EL DISCO {self.path}no existe")
            return 1

        c_println("Removiendo disco...")
        os.remove(self.path)
        return 0

