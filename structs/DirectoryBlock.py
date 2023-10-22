from structs.Content import Content
import struct

directory_block_binary_format_string = ">16s 16s 16s 16s"  # Cada Content usa 16bytes


class DirectoryBlock:
    def __init__(self, b_content=None):
        self.b_content = [Content() for _ in range(4)] if b_content is None else b_content

    def pack(self):
        return struct.pack(
            directory_block_binary_format_string,
            *[content.pack() for content in self.b_content]
        )

    def unpack(self, data):
        content_data = struct.unpack(directory_block_binary_format_string, data)
        for i, content in enumerate(self.b_content):
            content.unpack(content_data[i])
