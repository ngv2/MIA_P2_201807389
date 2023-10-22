import os
import struct
import time

from interface.Command import Command
from console.Console import c_println

from structs.EBR import EBR, ebr_binary_format_string
from structs.MBR import MBR, mbr_binary_format_string
from structs.SuperBlock import SuperBlock, super_block_binary_format_string
from fs_utils.FileSystemUtils import read_struct_from_stream, write_struct_to_stream


from general.PartitionMounting import PartitionMount, mount_new_partition, DiskMount


class MOUNT(Command):

    def __init__(self):
        self.args = {}
        self.path = ""
        self.name = ""

    def set_args(self, the_args):
        self.args = the_args

    def parse_args(self):
        for name, value in self.args.items():
            if name == "path":
                self.path = value
                continue
            if name == "name":
                self.name = value
                continue
            c_println("MOUNT->ARGUMENTO INVALIDO ", name)
            return 1

        if self.path == "":
            c_println("MOUNT->NO SE BRINDO EL ARGUMENTO PATH")
            return 1
        if self.name == "":
            c_println("MOUNT->NO SE BRINDO EL ARGUMENTO NAME")
            return 1
        return 0

    def run_command(self):
        parse_args_result = self.parse_args()
        if parse_args_result != 0:
            return parse_args_result

        if not os.path.isfile(self.path):
            c_println(f"MOUNT->ERROR EL ARCHIVO {self.path} NO EXISTE")
            return 1

        with open(self.path, 'rb+') as fs:
            mbr = MBR()
            fs.seek(0, os.SEEK_SET)
            read_struct_from_stream(fs, mbr, struct.calcsize(mbr_binary_format_string))

            for i, mbr_partition in enumerate(mbr.mbr_partitions):

                # Si la partición es extendida, se deben iterar todas las particiones lógicas para encontrar una
                if mbr_partition.part_status == b'T' and mbr_partition.part_type == b'E':
                    # Extendidas
                    if self.name == mbr_partition.part_name.decode("utf-8").rstrip('\x00'):
                        c_println("MOUNT->ADVERTENCIA-> MONTAR UNA PARTICIÓN EXTENDIDA ES SOLO PARA REPORTES")

                        if is_partition_mounted(self.path, mbr_partition.part_name.decode("utf-8").rstrip('\x00')):
                            c_println("MOUNT->ERROR->LA PARTICIÓN YA ESTA MONTADA")
                            return 1

                        extended_mount = PartitionMount(
                            filepath=self.path,
                            name=mbr_partition.part_name.decode("utf-8").rstrip('\x00'),
                            ebr_index=-1,
                            partition_start=mbr_partition.part_start,
                            partition_size=mbr_partition.part_s,
                            partition_type='E'
                        )

                        mount_new_partition(self.path, extended_mount)
                        c_println("MOUNT->Partición montada con éxito. Lista de discos montados:{")
                        for disk_m in DiskMount.mounted_disks.values():
                            for part_key, part_val in disk_m.partitions.items():
                                c_println(part_key, "<<-->>", disk_m.filepath, "<<-->>", part_val.name)
                        c_println("}")
                        return 0

                    # Lógicas
                    logic_mount = self.get_logic_partition_mount_by_name(fs, self.name, mbr_partition.part_start)
                    if logic_mount.ebr_index == -1:
                        continue

                    if is_partition_mounted(self.path, logic_mount.name):
                        c_println("MOUNT->ERROR->LA PARTICIÓN YA ESTA MONTADA")
                        return 1

                    logic_mount.filepath = self.path
                    mount_new_partition(self.path, logic_mount)
                    c_println("MOUNT->Partición montada con éxito. Lista de discos montados:{")
                    for disk_m in DiskMount.mounted_disks.values():
                        for part_key, part_val in disk_m.partitions.items():
                            c_println(part_key, "<<-->>", disk_m.filepath, "<<-->>", part_val.name)
                    c_println("}")

                    # Actualizar el tiempo de montado
                    fs.seek(logic_mount.partition_start, os.SEEK_SET)
                    filesystem_type = struct.unpack('>i', fs.read(4))[0]
                    if filesystem_type != 0:
                        super_block = SuperBlock()
                        fs.seek(logic_mount.partition_start, os.SEEK_SET)  # fs.seek(-4, os.SEEK_CUR)
                        read_struct_from_stream(fs, super_block, struct.calcsize(super_block_binary_format_string))

                        super_block.s_mount_time = int(time.time())
                        super_block.s_mnt_count += 1

                        fs.seek(logic_mount.partition_start)
                        write_struct_to_stream(fs, super_block)

                    return 0

                if mbr_partition.part_status != b'T' or self.name != mbr_partition.part_name.decode("utf-8").rstrip('\x00'):
                    continue

                if is_partition_mounted(self.path, mbr_partition.part_name.decode("utf-8").rstrip('\x00')):
                    c_println("MOUNT->ERROR->LA PARTICIÓN YA ESTA MONTADA")
                    return 1

                partition_mount = PartitionMount(
                    filepath=self.path,
                    name=mbr_partition.part_name.decode("utf-8").rstrip('\x00'),
                    ebr_index=-1,
                    partition_start=mbr_partition.part_start,
                    partition_size=mbr_partition.part_s,
                    partition_type='P'
                )

                mount_new_partition(self.path, partition_mount)
                c_println("MOUNT->Partición montada con éxito. Lista de discos montados:{")
                for disk_m in DiskMount.mounted_disks.values():
                    for part_key, part_val in disk_m.partitions.items():
                        c_println(part_key, "<<-->>", disk_m.filepath, "<<-->>", part_val.name)
                c_println("}")

                # Actualizar el tiempo de montado
                fs.seek(partition_mount.partition_start, os.SEEK_SET)
                filesystem_type = struct.unpack('>i', fs.read(4))[0]
                if filesystem_type != 0:
                    super_block = SuperBlock()
                    fs.seek(partition_mount.partition_start)
                    read_struct_from_stream(fs, super_block, struct.calcsize(super_block_binary_format_string))
                    super_block.s_mount_time = int(time.time())
                    super_block.s_mnt_count += 1

                    fs.seek(partition_mount.partition_start, os.SEEK_SET)  # fs.seek(-4, os.SEEK_CUR)
                    write_struct_to_stream(fs, super_block)

                return 0

            c_println(f"MOUNT->ERROR->LA PARTICIÓN {self.name} NO EXISTE")

    def get_logic_partition_mount_by_name(self, fs, part_name, first_ebr_start):
        ebr = EBR()
        fs.seek(first_ebr_start, os.SEEK_SET)
        read_struct_from_stream(fs, ebr, struct.calcsize(ebr_binary_format_string))

        if ebr.part_status == b'F':
            return PartitionMount(ebr_index=-1)

        # Si es la primera
        if ebr.part_name.decode("utf-8").rstrip('\x00') == part_name:
            return PartitionMount(
                name=ebr.part_name.decode("utf-8").rstrip('\x00'),
                partition_start=ebr.part_start,
                partition_size=ebr.part_s,
                partition_type='L'
            )

        index = 0
        # Si esta en medio (o al final)
        while ebr.part_next != 0:
            fs.seek(ebr.part_next, os.SEEK_SET)
            read_struct_from_stream(fs, ebr, struct.calcsize(ebr_binary_format_string))
            index += 1
            if ebr.part_name.decode("utf-8").rstrip('\x00') == part_name:
                return PartitionMount(
                    name=ebr.part_name.decode("utf-8").rstrip('\x00'),
                    ebr_index=index,
                    partition_start=ebr.part_start,
                    partition_size=ebr.part_s,
                    partition_type='L'
                )

        return PartitionMount(ebr_index=-1)


def is_partition_mounted(diskpath, part_name):
    if diskpath in DiskMount.mounted_disks:
        for partition in DiskMount.mounted_disks[diskpath].partitions.values():
            if partition.name == part_name:
                return True
    return False
