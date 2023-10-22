import struct

partition_binary_format_string = ">3B Q Q 16s"


class Partition:
    def __init__(self, part_status=b'0', part_type=b'0', part_fit=b'0', part_start=0, part_s=0, part_name=None):
        self.part_status = part_status
        self.part_type = part_type
        self.part_fit = part_fit
        self.part_start = part_start
        self.part_s = part_s
        self.part_name = bytearray(16) if part_name is None else part_name

    def pack(self):
        return struct.pack(
            partition_binary_format_string,
            ord(self.part_status),
            ord(self.part_type),
            ord(self.part_fit),
            self.part_start,
            self.part_s,
            self.part_name
        )

    def unpack(self, data):
        (
            self.part_status,
            self.part_type,
            self.part_fit,
            self.part_start,
            self.part_s,
            self.part_name
        ) = struct.unpack(partition_binary_format_string, data)

        self.part_status = bytes([self.part_status])
        self.part_type = bytes([self.part_type])
        self.part_fit = bytes([self.part_fit])
