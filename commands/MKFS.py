import math
import struct
import time

from interface.Command import Command
from general.PartitionMounting import get_partition_mount
from console.Console import c_println

from structs.SuperBlock import SuperBlock, super_block_binary_format_string
from structs.Inode import inode_binary_format_string
from structs.FileBlock import file_block_binary_format_string

from fs_utils.FileSystemUtils import write_struct_to_stream

from fs_utils.FileSystemUtils import initialize_file_system


class MKFS(Command):

    def __init__(self):
        self.args = {}
        self.id = ""
        self.type = "full"

    def set_args(self, the_args):
        self.args = the_args

    def parse_args(self):
        for name, value in self.args.items():
            if name == "id":
                self.id = value
                continue
            if name == "type":
                if value.lower() != "full":
                    c_println("MKFS->EL ARGUMENTO TYPE DEBE SER 'FULL'")
                    return 1
                continue
            c_println("MKFS->ARGUMENTO INVALIDO ", name)
            return 1

        if self.id == "":
            c_println("MKFS->NO SE BRINDO EL ARGUMENTO ID")
            return 1
        return 0

    def run_command(self):
        parse_args_result = self.parse_args()
        if parse_args_result != 0:
            return parse_args_result

        partition_mount = get_partition_mount(self.id)

        if partition_mount is None:
            c_println(f"MKFS->ERROR->LA PARTICIÓN {self.id} NO ESTÁ MONTADA")
            return 1

        if partition_mount.partition_type == 'E':
            c_println(f"MKFS->ERROR->LA PARTICIÓN NO {self.id} ES EXTENDIDA Y ES SOLO PARA REPORTES")
            return 1

        n = (partition_mount.partition_size - struct.calcsize(super_block_binary_format_string)) / (4 + struct.calcsize(inode_binary_format_string) + 3 * struct.calcsize(file_block_binary_format_string))
        n = math.floor(n)
        if n < 2:
            c_println("MKFS->ERROR->LA PARTICIÓN NO ES LO SUFICIENTEMENTE GRANDE PARA FORMATEARLA")
            return 1

        c_println(f"MKFS->n: {n}")
        super_block = SuperBlock(
            s_filesystem_type=1,
            s_inodes_count=n,
            s_blocks_count=3*n,
            s_free_inodes_count=n,
            s_free_blocks_count=3*n,
            s_mount_time=int(time.time()),
            s_unmount_time=int(time.time()),
            s_magic=0xEF53,
            s_inode_size=struct.calcsize(inode_binary_format_string),
            s_block_size=struct.calcsize(file_block_binary_format_string),
            s_bm_inode_start=partition_mount.partition_start + struct.calcsize(super_block_binary_format_string),
        )

        super_block.s_bm_block_start = super_block.s_bm_inode_start + n
        super_block.s_inode_start = super_block.s_bm_block_start + 3 * n
        super_block.s_block_start = super_block.s_inode_start + n * struct.calcsize(inode_binary_format_string)

        with open(partition_mount.filepath, "rb+") as fs:
            # Seek to the partition start
            fs.seek(partition_mount.partition_start, 0)
            write_struct_to_stream(fs, super_block)

            # Clean with 0's
            buffer = bytes([0] * 1024)

            # Buffers of 1024
            for _ in range((partition_mount.partition_size - struct.calcsize(super_block_binary_format_string)) // 1024):
                fs.write(buffer)

            # Remaining bytes
            for _ in range((partition_mount.partition_size - struct.calcsize(super_block_binary_format_string)) % 1024):
                fs.write(b'\x00')

            initialize_file_system(fs, partition_mount.partition_start)
            c_println("MKFS->PARTICIÓN FORMATEADA CON ÉXITO")
            return 0
