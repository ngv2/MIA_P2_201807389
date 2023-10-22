import struct

content_binary_format_string = ">12s i"


class Content:  # 16 bytes
    def __init__(self, b_name="", b_inode=0):
        self.b_name = bytearray(12) if b_name == "" else b_name
        if str(type(self.b_name)) == "<class 'list'>":
            new_array = bytearray(12)
            if str(type(self.b_name[0])) == "<class 'bytes'>":
                new_array[:len(self.b_name)] = [ord(c) for c in self.b_name]
            else:
                new_array[:len(self.b_name)] = self.b_name
            self.b_name = new_array
        self.b_inode = b_inode

    def pack(self):
        return struct.pack(content_binary_format_string, self.b_name, self.b_inode)

    def unpack(self, data):
        self.b_name, self.b_inode = struct.unpack(content_binary_format_string, data)
        self.b_name = bytearray(self.b_name)
        pass
