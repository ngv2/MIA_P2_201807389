import struct

inode_binary_format_string = ">i i I q q q 16i B i"


class Inode:
    def __init__(self, i_uid=0, i_gid=0, i_size=0, i_open_time=0, i_creation_time=0,
                 i_modify_time=0, i_block=None, i_type=b'0', i_perm=0):
        self.i_uid = i_uid
        self.i_gid = i_gid
        self.i_size = i_size
        self.i_open_time = i_open_time
        self.i_creation_time = i_creation_time
        self.i_modify_time = i_modify_time
        self.i_block = [0] * 16 if i_block is None else i_block
        self.i_type = i_type
        self.i_perm = i_perm

    def pack(self):
        return struct.pack(
            inode_binary_format_string,
            self.i_uid,
            self.i_gid,
            self.i_size,
            self.i_open_time,
            self.i_creation_time,
            self.i_modify_time,
            *self.i_block,
            ord(self.i_type),
            self.i_perm
        )

    def unpack(self, data):
        values = struct.unpack(inode_binary_format_string, data)
        (
            self.i_uid,
            self.i_gid,
            self.i_size,
            self.i_open_time,
            self.i_creation_time,
            self.i_modify_time,
            *self.i_block,
            self.i_type,
            self.i_perm
        ) = values

        self.i_type = bytes([self.i_type])
