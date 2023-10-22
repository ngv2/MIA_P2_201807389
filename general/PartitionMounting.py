from typing import Any

import utils.Utils


class DiskMount:
    mounted_disks = {}

    def __init__(self, filepath="", partitions=None, disk_number=0):
        if partitions is None:
            partitions = {}
        self.filepath = filepath
        self.partitions = partitions
        self.disk_number = disk_number


class PartitionMount:
    def __init__(self, filepath="", name="", ebr_index=0, partition_start=0, partition_size=0, partition_type=0):
        self.filepath = filepath
        self.name = name
        self.ebr_index = ebr_index
        self.partition_start = partition_start
        self.partition_size = partition_size
        self.partition_type = partition_type


def mount_new_partition(filepath, partition):
    next_name, next_number = get_next_partition_name_and_number(filepath)
    generated_id = "89" + str(next_number) + next_name
    the_disk = DiskMount.mounted_disks.get(filepath)
    if not the_disk:
        DiskMount.mounted_disks[filepath] = DiskMount(filepath=filepath, disk_number=next_number, partitions={generated_id: partition})
        return
    the_disk.partitions[generated_id] = partition
    return


def get_partition_mount(the_id) -> PartitionMount | None:
    for theDisk in DiskMount.mounted_disks.values():
        partition_mount = theDisk.partitions.get(the_id)
        if not partition_mount:
            continue
        return partition_mount
    return None


def get_next_partition_name_and_number(filepath):
    disk_mount = DiskMount.mounted_disks.get(filepath)
    if not disk_mount:
        return utils.Utils.get_filename_by_filepath(filepath, False), 1
    length = len(disk_mount.partitions)
    return utils.Utils.get_filename_by_filepath(filepath, False), length+1


def to_base26(n):
    base26_digits = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    result = ""
    while n > 0:
        r = n % 26
        n //= 26
        result = base26_digits[r] + result
    return result
