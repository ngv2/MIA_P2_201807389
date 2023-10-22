import structs.Partition
from structs.Partition import Partition
import struct
from typing import List

mbr_binary_format_string = ">Q q i B 140s"


class MBR:
    def __init__(self, mbr_size=0, mbr_creation_date=0, mbr_dsk_signature=0, dsk_fit=b'0', mbr_partitions=None):
        self.mbr_size = mbr_size
        self.mbr_creation_date = mbr_creation_date
        self.mbr_dsk_signature = mbr_dsk_signature
        self.dsk_fit = dsk_fit
        if mbr_partitions is None:
            self.mbr_partitions: List[Partition] = [Partition() for _ in range(4)]
        else:
            self.mbr_partitions: List[Partition] = mbr_partitions

    def pack(self):
        return struct.pack(
            mbr_binary_format_string,
            self.mbr_size,
            self.mbr_creation_date,
            self.mbr_dsk_signature,
            ord(self.dsk_fit),
            b''.join(partition.pack() for partition in self.mbr_partitions)
        )

    def unpack(self, data):
        (
            self.mbr_size,
            self.mbr_creation_date,
            self.mbr_dsk_signature,
            self.dsk_fit,
            partitions_data
        ) = struct.unpack(mbr_binary_format_string, data)

        self.dsk_fit = bytes([self.dsk_fit])

        partition_size = struct.calcsize(structs.Partition.partition_binary_format_string)
        for i in range(4):
            partition_data = partitions_data[i * partition_size:(i + 1) * partition_size]
            self.mbr_partitions[i].unpack(partition_data)
            self.mbr_partitions[i].part_name = bytearray(self.mbr_partitions[i].part_name)
