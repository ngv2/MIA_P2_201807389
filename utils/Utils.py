import html
from typing import BinaryIO


def read_struct_from_stream(fs: BinaryIO, the_struct, size):
    data = fs.read(size)
    the_struct.unpack(data)
    return 0


def write_struct_to_stream(fs: BinaryIO, the_struct):
    data = the_struct.pack()
    fs.write(data)
    fs.flush()
    return 0


def get_directory_name_by_filepath(filepath):
    pos = max(filepath.rfind('/'), filepath.rfind('\\'))
    if pos == -1:
        return ""
    return filepath[:pos]


def get_filename_by_filepath(filepath, include_extension):
    pos = max(filepath.rfind('/'), filepath.rfind('\\'))
    r = filepath
    if pos != -1:
        r = filepath[pos+1:]
    if include_extension:
        return r
    pos = r.rfind('.')
    if pos == -1:
        return ""
    return r[:pos]


def html_escape(input_str):
    return html.escape(input_str, quote=True)

# def read_mbr_from_stream(fs, mbr):
#     data = fs.read(struct.calcsize(mbr_binary_format_string))
#     mbr.unpack(data)
#     return 0
# 
# 
# def write_mbr_to_stream(fs, mbr):
#     data = mbr.pack()
#     fs.write(data)
#     return 0
#
# 
# def read_partition_from_stream(fs, partition):
#     data = fs.read(struct.calcsize(mbr_binary_format_string))
#     partition.unpack(data)
#     return 0
# 
# 
# def write_partition_to_stream(fs, partition):
#     data = partition.pack()
#     fs.write(data)
#     return 0
# 
# 
# def read_ebr_from_stream(fs, ebr):
#     data = fs.read(struct.calcsize(mbr_binary_format_string))
#     ebr.unpack(data)
#     return 0
# 
# 
# def write_ebr_to_stream(fs, ebr):
#     data = ebr.pack()
#     fs.write(data)
#     return 0
# 
# 
# def read_superblock_from_stream(fs, superblock):
#     data = fs.read(struct.calcsize(mbr_binary_format_string))
#     superblock.unpack(data)
#     return 0
# 
# 
# def write_superblock_to_stream(fs, superblock):
#     data = superblock.pack()
#     fs.write(data)
#     return 0
# 
# 
# def read_inode_from_stream(fs, inode):
#     data = fs.read(struct.calcsize(mbr_binary_format_string))
#     inode.unpack(data)
#     return 0
# 
# 
# def write_inode_to_stream(fs, inode):
#     data = inode.pack()
#     fs.write(data)
#     return 0
# 
# 
# def read_fileblock_from_stream(fs, fileblock):
#     data = fs.read(struct.calcsize(mbr_binary_format_string))
#     fileblock.unpack(data)
#     return 0
# 
# 
# def write_fileblock_to_stream(fs, fileblock):
#     data = fileblock.pack()
#     fs.write(data)
#     return 0
# 
# 
# def read_directory_block_from_stream(fs, directory_block):
#     data = fs.read(struct.calcsize(mbr_binary_format_string))
#     directory_block.unpack(data)
#     return 0
# 
# 
# def write_directory_block_to_stream(fs, directory_block):
#     data = directory_block.pack()
#     fs.write(data)
#     return 0
# 
















