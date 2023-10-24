import io
import os
import re
import struct

from interface.Command import Command
from console.Console import c_println

from general.PartitionMounting import get_partition_mount
from fs_utils.FileSystemUtils import get_file_content
from structs.SuperBlock import SuperBlock, super_block_binary_format_string
from general.LoggedUser import LoggedUser


class LOGIN(Command):

    def __init__(self):
        self.args = {}
        self.username = ""
        self.password = ""
        self.id = ""

    def set_args(self, the_args):
        self.args = the_args

    def parse_args(self):
        for name, value in self.args.items():
            if name == "user":
                self.username = value
                continue
            if name == "pass":
                self.password = value
                continue
            if name == "id":
                self.id = value
                continue
            c_println("LOGIN->ARGUMENTO INVALIDO ", name)
            return 1

        if self.username == "":
            c_println("LOGIN->NO SE BRINDO EL ARGUMENTO USER")
            return 1
        if self.password == "":
            c_println("LOGIN->NO SE BRINDO EL ARGUMENTO PASS")
            return 1
        if self.id == "":
            c_println("LOGIN->NO SE BRINDO EL ARGUMENTO ID")
            return 1
        return 0

    def run_command(self):
        parse_args_result = self.parse_args()
        if parse_args_result != 0:
            return parse_args_result

        if LoggedUser.username != "":
            c_println(f"YA HAY UNA SESIÓN INICIADA, SE DEBE CERRAR ANTES DE CONTINUAR")
            return -1

        partition_mount = get_partition_mount(self.id)

        if partition_mount is None:
            c_println(f"LOGIN->ERROR-> LA PARTICIÓN CON ID {self.id} NO ESTA MONTADA")
            return 1

        with open(partition_mount.filepath, 'rb+') as fs:
            fs.seek(partition_mount.partition_start, io.SEEK_SET)
            filesystem_type = struct.unpack('>i', fs.read(4))[0]

            if filesystem_type == 0:
                c_println(f"LOGIN->ERROR->LA PARTICIÓN CON ID {self.id} NO TIENE UN SISTEMA DE ARCHIVOS")
                return 1

            super_block = SuperBlock()
            fs.seek(partition_mount.partition_start, os.SEEK_SET)
            super_block_bytes = fs.read(struct.calcsize(super_block_binary_format_string))
            super_block.unpack(super_block_bytes)

            users_file = get_file_content(fs, super_block, 1)
            patter_string = r'^([1-9][0-9]*),U,([^,]*),' + re.escape(self.username) + r',([^\n]*)'
            active_user_pattern = re.compile(patter_string, re.MULTILINE)
            match = active_user_pattern.search(users_file)

            if match is None:
                c_println(f"LOGIN->ERROR-> EL USUARIO {self.username} NO EXISTE")
                return 1

            matched_uid, matched_group_name, matched_pass = match.groups()

            if self.password != matched_pass:
                c_println("LOGIN->ERROR->CONTRASEÑA INCORRECTA")
                return 1

            active_group_pattern = re.compile(r'^([0-9]*),G,' + re.escape(matched_group_name) + '\n', re.MULTILINE)
            match = active_group_pattern.search(users_file)

            if match is None:
                c_println("LOGIN->ERROR-> EL USUARIO PERTENECE A UN GRUPO QUE NO EXISTE")
                return 1

            if match.group(1) == "0":
                c_println("LOGIN->ERROR-> EL USUARIO PERTENECE A UN GRUPO DESHABILITADO")
                return 1

            LoggedUser.username = self.username
            LoggedUser.uid = int(matched_uid)
            LoggedUser.gid = int(match.group(1))
            LoggedUser.partition_id = self.id
            c_println("LOGIN->INICIO DE SESIÓN CON ÉXITO")
            return 0


