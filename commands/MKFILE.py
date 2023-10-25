import os
import struct
import time

from interface.Command import Command
from console.Console import c_println

from general.LoggedUser import LoggedUser
from general.PartitionMounting import get_partition_mount
from structs.SuperBlock import SuperBlock, super_block_binary_format_string
from structs.Inode import Inode, inode_binary_format_string
from structs.DirectoryBlock import DirectoryBlock, directory_block_binary_format_string
from structs.Content import Content
from fs_utils.FileSystemUtils import (read_struct_from_stream, write_struct_to_stream, get_element_inode_number,
                                      set_file_content, decompose_file_path, make_file, make_directories,
                                      get_next_free_inode, get_next_free_block, set_block_usage)


class MKFILE(Command):

    def __init__(self):
        self.args = {}
        self.path = ""
        self.create_parents = ""
        self.size = -1
        self.content = ""

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
            if name == "size":
                try:
                    val = int(value)
                except ValueError:
                    c_println("MKFILE->ERROR-> EL VALOR DE SIZE NO ES UN ENTERO")
                    return 1

                if val < 0:
                    c_println("MKFILE->ERROR-> EL VALOR DE SIZE DEBE SER UN ENTERO POSITIVO O 0")
                    return 1

                self.size = val
                continue
            if name == "cont":
                self.content = value
                continue

            c_println("MKFILE->ARGUMENTO INVALIDO ", name)
            return 1

        if self.path == "":
            c_println("MKFILE->NO SE BRINDO EL ARGUMENTO PATH")
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

        fs_start = super_block.s_bm_inode_start - super_block.s_inode_size

        directories = decompose_file_path(self.path)

        if len(directories) == 0:
            c_println("MKFILE->ERROR-> ARCHIVO NO ESPECIFICADO")
            return 1

        file_inode_number = get_element_inode_number(fs, super_block, 0, directories, 1)

        if file_inode_number == -2:
            return 1

        if file_inode_number != -1:
            c_println(f"MKFILE->ERROR-> EL ARCHIVO {self.path} YA EXISTE")
            return 1

        file_name = directories[-1]
        directories = directories[:-1]

        if self.create_parents:
            recursive_create_result = make_directories(partition_mount.filepath, super_block, 0, directories)

            if recursive_create_result != 0:
                return recursive_create_result

            # Actualizar el super bloque antes de proseguir
            fs.seek(partition_mount.partition_start, os.SEEK_SET)
            read_struct_from_stream(fs, super_block, struct.calcsize(super_block_binary_format_string))

        last_parent_inode_number = get_element_inode_number(fs, super_block, 0, directories, 0)

        if last_parent_inode_number == -1:
            c_println(f"MKFILE->ERROR-> LOS DIRECTORIOS PADRES DE {self.path} NO EXISTEN")
            return 1

        content = ""

        if self.content != "":
            if not os.path.isfile(self.content):
                c_println(f"MKFILE->ERROR-> EL ARCHIVO {self.content} NO EXISTE")
                return 10

            with open(self.content, 'r') as file:
                data = file.read()
                content = data
        else:
            for i in range(self.size):
                content += str(i % 10)

        next_free_inode = -1

        father_folder_inode = Inode()
        fs.seek(super_block.s_inode_start + last_parent_inode_number * struct.calcsize(inode_binary_format_string), os.SEEK_SET)
        read_struct_from_stream(fs, father_folder_inode, struct.calcsize(inode_binary_format_string))

        for i in range(16):
            if father_folder_inode.i_block[i] == -1:
                next_free_block2 = get_next_free_block(fs, fs_start)

                if next_free_block2 == -1:
                    c_println("FILESYSTEM->ERROR-> NO QUEDAN BLOQUES DISPONIBLES")
                    return 1

                set_block_usage(fs, fs_start, next_free_block2, 1)
                base_block = DirectoryBlock(b_content=[
                    Content(b_name=struct.pack("12s", "-".encode('ascii')), b_inode=-1),
                    Content(b_name=struct.pack("12s", "-".encode('ascii')), b_inode=-1),
                    Content(b_name=struct.pack("12s", "-".encode('ascii')), b_inode=-1),
                    Content(b_name=struct.pack("12s", "-".encode('ascii')), b_inode=-1)
                ])

                fs.seek(super_block.s_block_start + next_free_block2 * struct.calcsize(directory_block_binary_format_string), os.SEEK_SET)
                write_struct_to_stream(fs, base_block)

                # Update its pointer
                father_folder_inode.i_block[i] = next_free_block2
                father_folder_inode.i_modify_time = int(time.time())
                fs.seek(super_block.s_inode_start + last_parent_inode_number * struct.calcsize(inode_binary_format_string), os.SEEK_SET)
                write_struct_to_stream(fs, father_folder_inode)

            index = 0
            if i == 0:
                index = 2

            directory_block = DirectoryBlock()
            fs.seek(super_block.s_block_start + father_folder_inode.i_block[i] * struct.calcsize(directory_block_binary_format_string), os.SEEK_SET)
            read_struct_from_stream(fs, directory_block, struct.calcsize(directory_block_binary_format_string))

            for j in range(index, 4):
                if directory_block.b_content[j].b_inode != -1:
                    continue

                next_free_inode = get_next_free_inode(fs, partition_mount.partition_start)

                make_file_result = make_file(partition_mount.filepath, super_block, file_name, next_free_inode,
                                             partition_mount.partition_start, directory_block,
                                             int(father_folder_inode.i_block[i]), j, fs)

                if make_file_result != 0:
                    return make_file_result

                fs.seek(partition_mount.partition_start, os.SEEK_SET)
                read_struct_from_stream(fs, super_block, struct.calcsize(super_block_binary_format_string))

                father_folder_inode.i_modify_time = int(time.time())
                fs.seek(super_block.s_inode_start + last_parent_inode_number * struct.calcsize(inode_binary_format_string), os.SEEK_SET)
                write_struct_to_stream(fs, father_folder_inode)

                # Set file content
                make_result = set_file_content(fs, super_block, next_free_inode, content)

                if make_result != 0:
                    return make_result

                c_println(f"MKFILE->ARCHIVO {self.path} CREADO CON ÉXITO")
                return 0
        c_println(f"MKFILE->ERROR->NO SE PUDO CREAR EL ARCHIVO. LA CANTIDAD MAXIMA DE HIJOS ES 62")
        return 1
