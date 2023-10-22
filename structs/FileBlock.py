import struct

file_block_binary_format_string = ">64s"


class FileBlock:
    def __init__(self, b_content=None):
        self.b_content = bytearray(64) if b_content is None else b_content

    def pack(self):
        return struct.pack(file_block_binary_format_string, self.b_content)

    def unpack(self, data):
        self.b_content = bytearray(struct.unpack(file_block_binary_format_string, data)[0])
        pass
