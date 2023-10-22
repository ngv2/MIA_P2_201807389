import os
import time
import random
import io
from pathlib import Path

from structs.Partition import Partition
from structs.MBR import MBR
from interface.Command import Command
from utils.Utils import get_directory_name_by_filepath
from console.Console import c_println, c_print
from fs_utils.FileSystemUtils import write_struct_to_stream

# TODO set to false
allow_disk_override = True


class MKDISK(Command):

    def __init__(self):
        self.args = {}
        self.size = 0
        self.fit = 'F'
        self.unit = 'M'
        self.path = ""

    def set_args(self, the_args):
        self.args = the_args

    def parse_args(self):
        is_size_set = False
        for name, value in self.args.items():
            if name == "size":
                try:
                    val = int(value)
                    if val <= 0:
                        c_print("MKDISK::>ERROR: SIZE DEBE SER MAYOR QUE 0")
                        return -1
                    self.size = val
                    is_size_set = True
                    continue
                except ValueError:
                    print("MKDISK::>SIZE DEBE SER UN ENTERO")
                    return -1

            if name == "fit":
                value = value.upper()
                if value == "BF":
                    self.fit = 'B'
                elif value == "FF":
                    self.fit = 'F'
                elif value == "WF":
                    self.fit = 'W'
                else:
                    print("MKDISK::> ARGUMENTO INCORRECTO: FIT DEBE SER BF, FF O WF")
                    return -1
                continue

            if name == "unit":
                value = value.upper()
                if value == "K":
                    self.unit = 'K'
                elif value == "M":
                    self.unit = 'M'
                else:
                    c_println("MKDISK::> ARGUMENTO INCORRECTO: UNIT DEBE SER K O M")
                    return -1
                continue

            if name == "path":
                self.path = value
                continue

            c_println("MKDISK::>ARGUMENTO INVALIDO ", name)
            return -1

        # Argumentos obligatorios
        if self.path == "":
            c_println("MKDISK::>NO SE BRINDO EL ARGUMENTO PATH")
            return -1
        if not is_size_set:
            c_println("MKDISK::>NO SE BRINDO EL ARGUMENTO SIZE")
            return -1

        if self.unit == 'M':
            self.size *= 1024

        # B TO KB
        self.size *= 1024
        return 0

    def run_command(self):
        parse_args_result = self.parse_args()
        if parse_args_result != 0:
            return parse_args_result

        if os.path.isfile(self.path):
            if allow_disk_override:
                c_println("Disco ya existe, sobre escribiendo...")
            else:
                c_println("Disco ya existe, no se puede sobre escribir")
                return 1

        f_path = get_directory_name_by_filepath(self.path)
        Path(f_path).mkdir(parents=True, exist_ok=True)

        try:
            fs = open(self.path, "wb")
        except Exception as e:
            print(e)
            return -10

        buffer = bytes(1024)
        num_buffers = self.size // 1024
        for _ in range(num_buffers):
            fs.write(buffer)
        fs.flush()

        current_time = int(time.time())
        random_signature = random.randint(0, 2 ** 31 - 1)
        c_println("Firma aleatoria:" + str(random_signature))

        partition1 = Partition(part_status=b'F', part_type=b'P', part_fit=b'W', part_name=bytearray(16))
        partition2 = Partition(part_status=b'F', part_type=b'P', part_fit=b'W', part_name=bytearray(16))
        partition3 = Partition(part_status=b'F', part_type=b'P', part_fit=b'W', part_name=bytearray(16))
        partition4 = Partition(part_status=b'F', part_type=b'P', part_fit=b'W', part_name=bytearray(16))
        partition1.part_name[:1] = b'-'
        partition2.part_name[:1] = b'-'
        partition3.part_name[:1] = b'-'
        partition4.part_name[:1] = b'-'

        mbr = MBR(self.size, current_time, random_signature, self.fit, [partition1, partition2, partition3, partition4])

        with open(self.path, 'r+b') as fs:
            fs.seek(0, io.SEEK_SET)
            write_struct_to_stream(fs, mbr)
            fs.flush()
        return 0