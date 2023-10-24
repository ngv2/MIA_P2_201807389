import os
import re
import struct

from interface.Command import Command
from console.Console import c_println
from general.LoggedUser import LoggedUser
from general.PartitionMounting import get_partition_mount

from structs.SuperBlock import SuperBlock, super_block_binary_format_string
from fs_utils.FileSystemUtils import read_struct_from_stream, get_element_inode_number, get_file_content, set_file_content


class MKUSR(Command):

    def __init__(self):
        self.args = {}
        self.username = ""
        self.password = ""
        self.group = ""

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
            if name == "grp":
                self.group = value
                continue
            c_println("MKUSR->ARGUMENTO INVALIDO ", name)
            return 1

        if self.username == "":
            c_println("MKUSR->NO SE BRINDO EL ARGUMENTO USER")
            return 1
        if len(self.username) > 10:
            c_println("MKGRP->EL NOMBRE DEL USUARIO TIENE UN MÁXIMO DE 10 CARACTERES")
            return 1
        if self.password == "":
            c_println("MKUSR->NO SE BRINDO EL ARGUMENTO PASS")
            return 1
        if len(self.password) > 10:
            c_println("MKGRP->LA CONTRASEÑA TIENE UN MÁXIMO DE 10 CARACTERES")
            return 1
        if self.group == "":
            c_println("MKGRP->NO SE BRINDO EL ARGUMENTO GRP")
            return 1

        return 0

    def run_command(self):
        parse_args_result = self.parse_args()
        if parse_args_result != 0:
            return parse_args_result

        if LoggedUser.username == "":
            c_println("MKGRP->ERROR->NO HAY SESIÓN INICIADA")
            return 1

        if LoggedUser.uid != 1:
            c_println("MKGRP->ERROR->ESTE COMANDO SOLO PUEDE SER UTILIZADO POR EL USUARIO ROOT")
            return 1

        partition_mount = get_partition_mount(LoggedUser.partition_id)

        if partition_mount is None:
            c_println(f"MKFS->ERROR->LA PARTICIÓN CON ID {LoggedUser.partition_id} NO ESTA MONTADA")
            return 1

        if partition_mount.partition_type == 'E':
            c_println(f"MKFS->ERROR->LA PARTICIÓN {LoggedUser.partition_id} ES EXTENDIDA Y SOLO ES PARA REPORTES")
            return 1

        fs = open(partition_mount.filepath, "rb+")

        super_block = SuperBlock()
        fs.seek(partition_mount.partition_start, os.SEEK_SET)
        read_struct_from_stream(fs, super_block, struct.calcsize(super_block_binary_format_string))

        file_inode_number = get_element_inode_number(fs, super_block, 0, ["users.txt"], 1)

        if file_inode_number < 0:
            c_println("MKGRP->ERROR->ERROR DE SISTEMA. NO SE PUDO ENCONTRAR USERS.TXT")
            return 1

        users_file = get_file_content(fs, super_block, file_inode_number)

        active_user_regex = re.compile(r'[1-9][0-9]*,U,[^,]*,' + re.escape(self.username) + r',[^\n]*', re.MULTILINE)
        disabled_user_regex = re.compile(r'^0,U,[^,]*,' + re.escape(self.username) + ',[^\n]*', re.MULTILINE)
        active_group_regex = re.compile(r'[1-9][0-9]*,G,' + re.escape(self.group) + '\n', re.MULTILINE)

        match = active_group_regex.search(users_file)

        if match is None:
            c_println(f"MKUSR->ERROR->EL GRUPO {self.group} NO EXISTE")
            return 10

        match = active_user_regex.search(users_file)

        if match is not None:
            c_println(f"MKUSR->ERROR->EL USUARIO {self.username} YA EXISTE")
            return 10

        # Get next available UID
        any_active_group_pattern = re.compile(r'([1-9][0-9]*),U,[^\n]*', re.MULTILINE)
        next_available_uid = 0

        for match in any_active_group_pattern.finditer(users_file):
            n = int(match.group(1))
            if n > next_available_uid:
                next_available_uid = n

        next_available_uid += 1

        match2 = disabled_user_regex.search(users_file)

        if match2 is not None:
            start, end = match2.start(0), match2.end(0)
            users_file = users_file[:start] + str(next_available_uid) + f",U,{self.group},{self.username},{self.password}" + users_file[end:]
            update_r = set_file_content(fs, super_block, file_inode_number, users_file)

            if update_r != 0:
                return update_r

            c_println(f"MKUSR->USUARIO {self.username} RECREADO CON ÉXITO")
            c_println("Nuevo archivo users.txt:")
            c_println(users_file)
            return 0

        users_file += f"{next_available_uid},U,{self.group},{self.username},{self.password}\n"

        c_println("Nuevo archivo users.txt:")
        c_println(users_file)

        update_r = set_file_content(fs, super_block, file_inode_number, users_file)

        if update_r != 0:
            return update_r

        c_println(f"MKUSR->USUARIO {self.username} CREADO CON ÉXITO")

        return 0


