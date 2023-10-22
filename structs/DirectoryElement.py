class DirectoryElement:  # No usado directamente en disco?
    def __init__(self, is_directory, name, inode_number):
        self.IsDirectory = is_directory  # 1 byte
        self.Name = name  # string
        self.InodeNumber = inode_number  # 4 byte int
