import os
import re
import struct
from interface.Command import Command
from console.Console import c_println
from general.LoggedUser import LoggedUser
from general.PartitionMounting import get_partition_mount

from structs.SuperBlock import SuperBlock, super_block_binary_format_string
from fs_utils.FileSystemUtils import read_struct_from_stream, get_element_inode_number, get_file_content, set_file_content


class RMGRP(Command):

    def __init__(self):
        self.args = {}
        self.name = ""

    def set_args(self, the_args):
        self.args = the_args

    def parse_args(self):
        for name, value in self.args.items():
            if name == "name":
                self.name = value
                continue
            c_println("RMGRP->ARGUMENTO INVALIDO ", name)
            return 1

        if self.name == "":
            c_println("RMGRP->NO SE BRINDO EL ARGUMENTO NAME")
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

        active_group_regex = re.compile(r'^([1-9][0-9]*),G,' + re.escape(self.name) + '\n', re.MULTILINE)
        disabled_group_regex = re.compile(r'^0,G,' + re.escape(self.name) + '\n', re.MULTILINE)

        match = disabled_group_regex.search(users_file)

        if match is not None:
            c_println(f"RMGRP->ERROR->EL GRUPO {self.name} FUE BORRADO ANTERIORMENTE")
            return 1

        match2 = active_group_regex.search(users_file)

        if match2 is not None:
            start, end = match2.start(1), match2.end(1)
            users_file = users_file[:start] + '0' + users_file[end:]
            update_r = set_file_content(fs, super_block, file_inode_number, users_file)

            if update_r != 0:
                return update_r

            c_println(f"RMGRP->GRUPO {self.name} BORRADO CON ÉXITO")
            return 0

        c_println(f"RMGRP->ERROR-> EL GRUPO {self.name} NO EXISTE")
        return 8


