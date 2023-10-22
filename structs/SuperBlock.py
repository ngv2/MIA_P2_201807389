import struct

super_block_binary_format_string = ">5i 2q 1I 1i 2I 2i 4Q"


class SuperBlock:
    def __init__(self, s_filesystem_type=0, s_inodes_count=0, s_blocks_count=0,
                 s_free_inodes_count=0, s_free_blocks_count=0, s_mount_time=0,
                 s_unmount_time=0, s_mnt_count=0, s_magic=0, s_inode_size=0,
                 s_block_size=0, s_first_inode=0, s_first_block=0,
                 s_bm_inode_start=0, s_bm_block_start=0, s_inode_start=0,
                 s_block_start=0):
        self.s_filesystem_type = s_filesystem_type
        self.s_inodes_count = s_inodes_count
        self.s_blocks_count = s_blocks_count
        self.s_free_inodes_count = s_free_inodes_count
        self.s_free_blocks_count = s_free_blocks_count
        self.s_mount_time = s_mount_time
        self.s_unmount_time = s_unmount_time
        self.s_mnt_count = s_mnt_count
        self.s_magic = s_magic
        self.s_inode_size = s_inode_size
        self.s_block_size = s_block_size
        self.s_first_inode = s_first_inode
        self.s_first_block = s_first_block
        self.s_bm_inode_start = s_bm_inode_start
        self.s_bm_block_start = s_bm_block_start
        self.s_inode_start = s_inode_start
        self.s_block_start = s_block_start

    def pack(self):
        return struct.pack(
            super_block_binary_format_string,
            self.s_filesystem_type,
            self.s_inodes_count,
            self.s_blocks_count,
            self.s_free_inodes_count,
            self.s_free_blocks_count,
            self.s_mount_time,
            self.s_unmount_time,
            self.s_mnt_count,
            self.s_magic,
            self.s_inode_size,
            self.s_block_size,
            self.s_first_inode,
            self.s_first_block,
            self.s_bm_inode_start,
            self.s_bm_block_start,
            self.s_inode_start,
            self.s_block_start
        )

    def unpack(self, data):
        (
            self.s_filesystem_type,
            self.s_inodes_count,
            self.s_blocks_count,
            self.s_free_inodes_count,
            self.s_free_blocks_count,
            self.s_mount_time,
            self.s_unmount_time,
            self.s_mnt_count,
            self.s_magic,
            self.s_inode_size,
            self.s_block_size,
            self.s_first_inode,
            self.s_first_block,
            self.s_bm_inode_start,
            self.s_bm_block_start,
            self.s_inode_start,
            self.s_block_start
        ) = struct.unpack(super_block_binary_format_string, data)
