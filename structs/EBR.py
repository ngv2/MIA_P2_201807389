import struct

ebr_binary_format_string = ">B B Q Q Q 16s"


class EBR:
    def __init__(self, part_status=b'F', part_fit=b'0', part_start=0, part_s=0, part_next=0, part_name=None):
        self.part_status = part_status
        self.part_fit = part_fit
        self.part_start: int = part_start
        self.part_s: int = part_s
        self.part_next: int = part_next
        self.part_name = bytearray(16) if part_name is None else part_name

    def pack(self):
        return struct.pack(
            ebr_binary_format_string,
            ord(self.part_status),
            ord(self.part_fit),
            self.part_start,
            self.part_s,
            self.part_next,
            self.part_name
        )

    def unpack(self, data):
        (
            self.part_status,
            self.part_fit,
            self.part_start,
            self.part_s,
            self.part_next,
            self.part_name
        ) = struct.unpack(ebr_binary_format_string, data)

        self.part_status = bytes([self.part_status])
        self.part_fit = bytes([self.part_fit])
        self.part_name = bytearray(self.part_name)

