import os
import struct

from interface.Command import Command
from console.Console import c_println

from general.LoggedUser import LoggedUser
from general.PartitionMounting import get_partition_mount
from structs.SuperBlock import SuperBlock, super_block_binary_format_string
from fs_utils.FileSystemUtils import (read_struct_from_stream, get_element_inode_number,
                                      decompose_file_path, make_directories)


class MKDIR(Command):

    def __init__(self):
        self.args = {}
        self.path = ""
        self.create_parents = False

    def set_args(self, the_args):
        self.args = the_args

    def parse_args(self):
        for name, value in self.args.items():
            if name == "path":
                self.path = value
                continue
            if name == "r":
                self.create_parents = True
                continue
            c_println("MKDIR->ARGUMENTO INVALIDO ", name)
            return 1

        if self.path == "":
            c_println("MKDIR->NO SE BRINDO EL ARGUMENTO PATH")
            return 1
        return 0

    def run_command(self):
        parse_args_result = self.parse_args()
        if parse_args_result != 0:
            return parse_args_result

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

        directories = decompose_file_path(self.path)

        dir_inode_number = get_element_inode_number(fs, super_block, 0, directories, 1)

        if dir_inode_number == -2:
            return 1

        if dir_inode_number != -1:
            c_println(f"MKDIR->ERROR->EL ARCHIVO {self.path} YA EXISTE")
            return 1

        if self.create_parents or len(directories) == 1:
            recursive_result = make_directories(partition_mount.filepath, super_block, 0, directories)

            if recursive_result != 0:
                return recursive_result

            c_println(f"MKDIR->DIRECTORIO {self.path} CREADO CON ÉXITO")
            return 0

        # Revisar que todos los directorios padres existan
        dir_to_create = directories[-1]
        directories = directories[:-1]

        last_parent_inode_number = get_element_inode_number(fs, super_block, 0, directories, 0)

        if last_parent_inode_number == -2:
            return 1

        if last_parent_inode_number == -1:
            c_println(f"MKDIR'>ERROR-> DIRECTORIOS PADRES DE {self.path} NO EXISTEN")
            return 1

        directories = [dir_to_create]
        make_result = make_directories(partition_mount.filepath, super_block, last_parent_inode_number, directories)

        if make_result != 0:
            return make_result

        c_println(f"MKDIR->DIRECTORIO {self.path} CREADO CON ÉXITO")
        return 0

