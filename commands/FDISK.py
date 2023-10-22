import io
import math
import os
import struct

from interface.Command import Command
from console.Console import c_println
from structs.EBR import EBR, ebr_binary_format_string
from structs.MBR import MBR, mbr_binary_format_string
from structs.Partition import Partition
from fs_utils.FileSystemUtils import read_struct_from_stream, write_struct_to_stream


class FDISK(Command):

    def __init__(self):
        self.args = {}
        self.size = 0
        self.unit = 'K'
        self.disk_type = b'P'
        self.fit = b'W'
        self.path = ""
        self.name = ""

    def set_args(self, the_args):
        self.args = the_args

    def parse_args(self):

        is_size_set = False
        for name, value in self.args.items():
            if name == "size":
                try:
                    val = int(value)
                except ValueError:
                    c_println("FDISK->SIZE DEBE SER UN ENTERO")
                    return -2
                self.size = val
                is_size_set = True
                continue
            if name == "unit":
                value_upper = value.upper()
                if value_upper not in ["B", "K", "M"]:
                    c_println("FDISK-> VALOR INVALIDO: UNIT DEBE SER B,K o M")
                    return 2
                self.unit = value_upper
                continue
            if name == "path":
                self.path = value
                continue
            if name == "type":
                value_upper = value.upper()
                if value_upper not in ["P", "E", "L"]:
                    c_println("FDISK-> VALOR INVALIDO: TYPE DEBE SER P,E o L")
                    return 2
                self.disk_type = bytes(value_upper.encode("ascii"))
                continue
            if name == "fit":
                value_upper = value.upper()
                if value_upper not in ["BF", "FF", "WF"]:
                    c_println("FDISK-> VALOR INVALIDO: FIT DEBE SER B, F o W")
                    return 2
                self.fit = bytes(value_upper[0].encode("ascii"))
                continue
            if name == "name":
                self.name = value[:16]
                continue

            c_println(f"FDISK->ARGUMENTO INVALIDO <{name}>")
            return 1

        if self.path == "":
            c_println("FDISK->NO SE BRINDO EL ARGUMENTO PATH")
            return 1

        if not is_size_set:
            c_println(f"FDISK->ARGUMENTO OBLIGATORIO size NO FUE DADO")
            return 1

        if self.size <= 0:
            c_println(f"SIZE DEBE SER MAYOR QUE 0")
            return 1

        if self.unit == 'M':
            self.size *= 1024 * 1024
        elif self.unit == 'K':
            self.size *= 1024
        return 0

    def run_command(self):
        parse_args_result = self.parse_args()
        if parse_args_result != 0:
            return parse_args_result
        return self.create_partition()

    def create_partition(self):
        if not os.path.isfile(self.path):
            c_println(f"FDISK->ERROR EL ARCHIVO {self.path} NO EXISTE")
            return 1
        c_println(f"Leyendo disco en {self.path}")

        with open(self.path, 'rb+') as fs:
            mbr = MBR()
            fs.seek(0, io.SEEK_SET)
            read_struct_from_stream(fs, mbr, struct.calcsize(mbr_binary_format_string))

            left = any(part.part_status == b'F' for part in mbr.mbr_partitions)
            if not left and self.disk_type != b'L':
                c_println("FDISK->ERROR-> EL DISCO YA TIENE 4 PARTICIONES PRIMARIAS/EXTENDIDAS")
                return 1

            # Caso especial de ninguna partición creada
            if mbr.mbr_partitions[0].part_status == b'F':
                if self.disk_type == b'L':
                    c_println("FDISK->ERROR-> UNA PARTICIÓN EXTENDIDA DEBE SER CREADA ANTES QUE UNA LOGICA")
                    return 1

                space = mbr.mbr_size - struct.calcsize(mbr_binary_format_string)
                if space < self.size:
                    c_println("FDISK->ERROR-> NO HAY ESPACIO DISPONIBLE PARA LA PARTICIÓN DESEADA")
                    return 1

                mbr.mbr_partitions[0].part_status = b'T'
                mbr.mbr_partitions[0].part_type = self.disk_type
                mbr.mbr_partitions[0].part_fit = self.fit
                mbr.mbr_partitions[0].part_start = struct.calcsize(mbr_binary_format_string)
                mbr.mbr_partitions[0].part_s = self.size
                mbr.mbr_partitions[0].part_name[:len(self.name)] = [ord(element) for element in self.name]

                fs.seek(0, io.SEEK_SET)
                write_struct_to_stream(fs, mbr)

                if self.disk_type == b'E':
                    ebr = EBR(b'F', self.fit)
                    ebr.part_name[0] = b'-'
                    write_struct_to_stream(fs, ebr)

                return 0

            for mbr_partition in mbr.mbr_partitions:
                if mbr_partition.part_status == b'T' and mbr_partition.part_type == b'E':
                    # Revisar solo una extendida
                    if self.disk_type == b'E':
                        c_println("FDISK::>ERROR: YA EXISTE UNA PARTICIÓN EXTENDIDA")
                        return 1
                    if self.disk_type == b'L':
                        first_ebr_pos = mbr_partition.part_start
                        extended_part_size = mbr_partition.part_s
                        extended_exist = True

                    if is_name_in_extended(fs, self.name, mbr_partition.part_start):
                        c_println("FDISK::>ERROR: UNA PARTICIÓN LOGICA CON ESTE NOMBRE YA EXISTE")
                        return 1

                if mbr_partition.part_status == b'T' and mbr_partition.part_name.decode("utf-8").rstrip('\x00') == self.name:
                    c_println("FDISK::>ERROR: UNA PARTICIÓN CON ESTE NOMBRE YA EXISTE")
                    return 1

            if self.disk_type == b'L':
                if not extended_exist:
                    c_println("FDISK::>ERROR: UNA PARTICIÓN LOGICA REQUIERE UNA PARTICIÓN EXTENDIDA PARA SER CREADA")
                    return 1
                return self.insert_logic_partition(first_ebr_pos, extended_part_size)

            sectors = [[0, 0, 0] for _ in range(4)]
            current_disk_position = struct.calcsize(mbr_binary_format_string)

            # Para salir mas fácil del ciclo sin un return o lugar especial
            while True:
                # En este punto, al menos la primera partición esta garantizada en existir
                # Sector 1: MargenIzquierdo <-> espacio Partición1
                sectors[0][0] = 1
                sectors[0][1] = current_disk_position
                sectors[0][2] = mbr.mbr_partitions[0].part_start - current_disk_position

                current_disk_position = mbr.mbr_partitions[0].part_start + mbr.mbr_partitions[0].part_s

                # Sector 2: Partición1 <-> Partición2 or Partición1 <-> MargenDerecho
                if mbr.mbr_partitions[1].part_status == b'T':
                    sectors[1][0] = 1
                    sectors[1][1] = current_disk_position
                    sectors[1][2] = mbr.mbr_partitions[1].part_start - current_disk_position
                else:
                    sectors[1][0] = 1
                    sectors[1][1] = current_disk_position
                    sectors[1][2] = mbr.mbr_size - current_disk_position
                    break  # Si la partición 2 no existe, entonces ninguna otra

                current_disk_position = mbr.mbr_partitions[1].part_start + mbr.mbr_partitions[1].part_s

                # Sector 3: Partición2 <-> Partición3 or Partición2 <-> MargenDerecho
                if mbr.mbr_partitions[2].part_status == b'T':
                    sectors[2][0] = 1
                    sectors[2][1] = current_disk_position
                    sectors[2][2] = mbr.mbr_partitions[2].part_start - current_disk_position
                else:
                    sectors[2][0] = 1
                    sectors[2][1] = current_disk_position
                    sectors[2][2] = mbr.mbr_size - current_disk_position
                    break  # Si la partición 3 no existe, entonces ninguna otra

                current_disk_position = mbr.mbr_partitions[2].part_start + mbr.mbr_partitions[2].part_s

                # Sector 4: Partición3 <-> MargenDerecho
                sectors[3][0] = 1
                sectors[3][1] = current_disk_position
                sectors[3][2] = mbr.mbr_size - current_disk_position
                break

            index_of_min = -1
            found_size = 0  # TODO no es necesaria?

            if mbr.dsk_fit == b'F':
                for sector in sectors:
                    if sector[0] == 0:
                        break
                    if sector[2] < self.size:
                        continue
                    self.insert_partition_and_reorder(mbr, sector[1])
                    return 0

                # Si no se encontró, no hay espacio para el disco
                c_println("FDISK::>ERROR: NO HAY SECTOR SUFICIENTEMENTE GRANDE PARA LA PARTICIÓN DESEADA")
                return 1

            elif mbr.dsk_fit == b'B':
                found_size = math.inf
                for i in range(4):
                    if sectors[i][0] == 0:
                        break
                    if self.size <= sectors[i][2] < found_size:
                        found_size = sectors[i][2]
                        index_of_min = i
                if index_of_min == -1:
                    c_println("FDISK::>ERROR: NO HAY SECTOR SUFICIENTEMENTE GRANDE PARA LA PARTICIÓN DESEADA")
                    return 1

                self.insert_partition_and_reorder(mbr, sectors[index_of_min][1])
                return 0

            elif mbr.dsk_fit == b'W':
                found_size = 0
                for i in range(4):
                    if sectors[i][0] == 0:
                        break
                    if sectors[i][2] >= self.size and sectors[i][2] > found_size:
                        found_size = sectors[i][2]
                        index_of_min = i
                if index_of_min == -1:
                    c_println("FDISK::>ERROR: NO HAY SECTOR SUFICIENTEMENTE GRANDE PARA LA PARTICIÓN DESEADA")
                    return 1

                self.insert_partition_and_reorder(mbr, sectors[index_of_min][1])
                return 0

            return -1

    def insert_logic_partition(self, first_ebr_start, extended_partition_size):
        with open(self.path, 'r+b') as fs:

            ebr = EBR()
            fs.seek(first_ebr_start, io.SEEK_SET)
            read_struct_from_stream(fs, ebr, struct.calcsize(ebr_binary_format_string))

            current_pos = first_ebr_start
            space = 0
            # Caso de ninguna partición logica existente
            if ebr.part_status == b'F':
                space = extended_partition_size - struct.calcsize(ebr_binary_format_string)

                if space < self.size:
                    c_println("FDISK->ERROR-> NO HAY ESPACIO SUFICIENTE PARA LA NUEVA PARTICIÓN")
                    return 1

                ebr.part_status = b'T'
                ebr.part_fit = self.fit
                ebr.part_start = current_pos + struct.calcsize(ebr_binary_format_string)
                ebr.part_s = self.size
                # El siguiente sigue siendo -1
                ebr.part_name[:len(self.name)] = [ord(element) for element in self.name]
                fs.seek(first_ebr_start, io.SEEK_SET)
                write_struct_to_stream(fs, ebr)
                return 0

            last_start = first_ebr_start
            last = ebr

            while last.part_next != 0:
                last_start = last.part_next
                fs.seek(last.part_next, io.SEEK_SET)
                read_struct_from_stream(fs, last, struct.calcsize(ebr_binary_format_string))

            space = (first_ebr_start + extended_partition_size) - (last.part_start + last.part_s) - struct.calcsize(ebr_binary_format_string)

            if space < self.size:
                c_println("FDISK->ERROR-> NO HAY ESPACIO SUFICIENTE PARA LA PARTICIÓN NUEVA")
                return 1

            # Actualizar el puntero del ultimo ebr al nuevo
            last.part_next = last_start + struct.calcsize(ebr_binary_format_string) + last.part_s
            fs.seek(last_start, io.SEEK_SET)
            write_struct_to_stream(fs, last)

            # Escribir nuevo EBR
            new_ebr = EBR(b'T', self.fit, last.part_next + struct.calcsize(ebr_binary_format_string),
                          self.size, 0, bytearray(16))
            new_ebr.part_name[:len(self.name)] = [ord(element) for element in self.name]
            fs.seek(last.part_next, io.SEEK_SET)
            write_struct_to_stream(fs, new_ebr)
            return 0

    def insert_partition_and_reorder(self, mbr: MBR, start):
        with open(self.path, 'r+b') as fs:

            found_index = -1
            last_visited = -1
            for i, partition in enumerate(mbr.mbr_partitions):
                last_visited = i

                if partition.part_status == b'F':
                    break

                if start >= partition.part_start:
                    continue

                found_index = i
                break

            # Caso de ser el ultimo
            if found_index == -1:
                last_partition: Partition = mbr.mbr_partitions[last_visited]
                last_partition.part_status = b'T'
                last_partition.part_type = self.disk_type
                last_partition.part_fit = self.fit
                last_partition.part_start = start
                last_partition.part_s = self.size
                last_partition.part_name[:len(self.name)] = [ord(element) for element in self.name]

                fs.seek(0, io.SEEK_SET)
                write_struct_to_stream(fs, mbr)

                if self.disk_type == b'E':
                    ebr = EBR(part_status=b'F', part_fit=self.fit)
                    ebr.part_name[:1] = b'-'
                    current_pos = start
                    fs.seek(current_pos, io.SEEK_SET)
                    write_struct_to_stream(fs, ebr)
                return

            # Hacer espacio para el siguiente
            for i in range(3, found_index - 1, -1):
                # Intercambiar orden
                mbr.mbr_partitions[i], mbr.mbr_partitions[i+1] = mbr.mbr_partitions[i+1], mbr.mbr_partitions[i]

            found_partition: Partition = mbr.mbr_partitions[found_index]
            found_partition.part_status = b'T'
            found_partition.part_type = self.disk_type
            found_partition.part_fit = self.fit
            found_partition.part_start = start
            found_partition.part_s = self.size
            found_partition.part_name[:len(self.name)] = [ord(element) for element in self.name]

            fs.seek(0, io.SEEK_SET)
            # TODO check if passed by reference in found_partition: Partition = mbr.mbr_partitions[found_index]
            #  If not, do mbr.mbr_partitions[found_index] = found_partition before
            write_struct_to_stream(fs, found_partition)

            if self.disk_type == 'E':
                ebr = EBR(part_status='F')
                ebr.part_name[0] = b'-'
                current_pos = start
                fs.seek(current_pos, io.SEEK_SET)
                write_struct_to_stream(fs, ebr)

    def get_far_most_byte_of_logic_partitions(self, fs, first_ebr_start):
        far_most = first_ebr_start
        ebr = EBR()
        fs.seek(first_ebr_start, io.SEEK_SET)
        read_struct_from_stream(fs, ebr, struct.calcsize(ebr_binary_format_string))

        if ebr.part_status == b'F':
            return far_most

        far_most = ebr.part_start + ebr.part_s

        while ebr.part_next != 0:
            fs.seek(ebr.part_next, io.SEEK_SET)
            read_struct_from_stream(fs, ebr, struct.calcsize(ebr_binary_format_string))
            candidate = ebr.part_start + ebr.part_s
            if candidate > far_most:
                far_most = candidate

        return far_most

    def get_close_most_byte_of_logic_partitions(self, fs, first_ebr_start, min_byte):
        ebr = EBR()
        fs.seek(first_ebr_start, io.SEEK_SET)
        read_struct_from_stream(fs, ebr, struct.calcsize(ebr_binary_format_string))
        close_most = ebr.part_start + ebr.part_s + 1  # +1 por si acaso para evitar exacto el mismo punto

        if ebr.part_status == b'F':
            return close_most
        close_most = ebr.part_start + ebr.part_s

        while ebr.part_next != 0:
            fs.seek(ebr.part_next, io.SEEK_SET)
            read_struct_from_stream(fs, ebr, struct.calcsize(ebr_binary_format_string))

            candidate = ebr.part_start + ebr.part_s
            if min_byte < candidate < close_most:
                close_most = candidate

        return close_most


def is_name_in_extended(fs, part_name, first_ebr_start):
    ebr = EBR()
    fs.seek(first_ebr_start, io.SEEK_SET)
    read_struct_from_stream(fs, ebr, struct.calcsize(ebr_binary_format_string))

    if ebr.part_status == b'F':
        return False

    if ebr.part_name.decode("utf-8").rstrip('\x00') == part_name:
        return True

    while ebr.part_next != 0:
        fs.seek(ebr.part_next, io.SEEK_SET)
        read_struct_from_stream(fs, ebr, struct.calcsize(ebr_binary_format_string))
        if ebr.part_name.decode("utf-8").rstrip('\x00') == part_name:
            return True

    return False
