import io
import os
import struct
import subprocess
import time

from interface.Command import Command
from console.Console import c_println
from general.PartitionMounting import get_partition_mount
from utils.Utils import get_directory_name_by_filepath, get_filename_by_filepath
from fs_utils.FileSystemUtils import read_struct_from_stream, get_element_inode_number, get_file_content, decompose_file_path
from structs.MBR import MBR, mbr_binary_format_string
from structs.EBR import EBR, ebr_binary_format_string
from structs.DirectoryBlock import DirectoryBlock, directory_block_binary_format_string
from structs.FileBlock import FileBlock, file_block_binary_format_string
from structs.Inode import Inode, inode_binary_format_string
from structs.SuperBlock import SuperBlock, super_block_binary_format_string

from structs.Partition import Partition

pixel_constant = 30


class REP(Command):

    def __init__(self):
        self.args = {}
        self.name = ""
        self.path = ""
        self.id = ""
        self.ruta = ""

    def set_args(self, the_args):
        self.args = the_args

    def parse_args(self):
        for name, value in self.args.items():
            if name == "name":
                self.name = value
                continue
            if name == "path":
                self.path = value
                continue
            if name == "id":
                self.id = value
                continue
            if name == "ruta":
                self.ruta = value
                continue
            c_println("REP->ARGUMENTO INVALIDO ", name)
            return 1

        if self.name == "":
            c_println("REP->NO SE BRINDO EL ARGUMENTO NAME")
            return 1
        if self.path == "":
            c_println("REP->NO SE BRINDO EL ARGUMENTO PATH")
            return 1
        if self.id == "":
            c_println("REP->NO SE BRINDO EL ARGUMENTO ID")
            return 1
        return 0

    def run_command(self):
        parse_args_result = self.parse_args()
        if parse_args_result != 0:
            return parse_args_result

        os.makedirs("./archivos_reportes", exist_ok=True)

        partition_mount = get_partition_mount(self.id)
        if partition_mount is None:
            c_println(f"REP->ERROR->LA PARTICIÓN {self.id} NO ESTA MONTADA")
            return 5

        with open(partition_mount.filepath, "rb+") as fs:
            if self.name == "mbr":
                reporte_string = generate_mbr_report(partition_mount.filepath)
                save_image_report(reporte_string, self.path)
                return 0
            if self.name == "disk":
                reporte_string = generate_disk_report(fs)
                save_image_report(reporte_string, self.path)
                return 0
            if self.name == "bm_inode":
                reporte_string = generate_bitmap_inode_report(fs, partition_mount.partition_start)
                save_image_report(reporte_string, self.path)
                return 0
            if self.name == "bm_block":
                reporte_string = generate_bitmap_block_report(fs, partition_mount.partition_start)
                save_image_report(reporte_string, self.path)
                return 0
            if self.name == "tree":
                reporte_string = generate_tree_report(self.id, fs, partition_mount.filepath, partition_mount.partition_start)
                save_image_report(reporte_string, self.path)
                return 0
            if self.name == "sb":
                reporte_string = generate_super_block_report(self.id, fs, partition_mount.filepath, partition_mount.partition_start)
                save_image_report(reporte_string, self.path)
                return 0
            if self.name == "file":
                reporte_string = generate_file_report(self.id, fs, partition_mount.partition_start, self.ruta)

                f_path = "./reportes/" + self.path.lstrip("./")
                print("Path nuevo:", f_path)
                os.makedirs(get_directory_name_by_filepath(f_path), exist_ok=True)
                with open(f_path, "w+") as ofs:
                    ofs.write(reporte_string)

                return 0

        c_println("REP->ERROR->TIPO DESCONOCIDO DE REPORTE")
        return -1


def save_image_report(graph, save_path):
    f_path = get_directory_name_by_filepath(save_path)

    if f_path != "":
        os.makedirs(f_path, exist_ok=True)
    os.makedirs("./archivos_reportes/", exist_ok=True)
    with open("./archivos_reportes/" + get_filename_by_filepath(save_path, True) + ".dot", "w") as fs:
        fs.write(graph)

    save_path = "./reportes/" + save_path.lstrip("./")
    print("Path nuevo:", save_path)
    os.makedirs(get_directory_name_by_filepath(save_path), exist_ok=True)

    if os.name == "nt":  # Si es en windows
        cmd = [
            "dot",
            "-Tsvg",
            "archivos_reportes\\" + get_filename_by_filepath(save_path, True) + ".dot",
            "-o",
            save_path.replace("/", "\\") + ".svg",
        ]
    else:
        cmd = [
            "dot",
            "-Tsvg",
            "./archivos_reportes/" + get_filename_by_filepath(save_path, True) + ".dot",
            "-o",
            save_path + ".svg",
        ]

    print(' '.join(cmd))
    try:
        subprocess.run(cmd, check=True, text=True)
    except subprocess.CalledProcessError as e:
        c_println(str(e))


def generate_inode_graphviz(fs, inode_number, super_block):
    inode = Inode()
    fs.seek(super_block.s_inode_start + inode_number * struct.calcsize(inode_binary_format_string), io.SEEK_SET)
    read_struct_from_stream(fs, inode, struct.calcsize(inode_binary_format_string))

    graph = ["inode", str(inode_number),
             "[label=< <table cellspacing=\"0\" border=\"1\" bgcolor=\"dodgerblue\">\n",
             "<tr><td colspan=\"2\" PORT=\"title\">Inodo #",
             str(inode_number),
             "</td></tr>\n",
             "<tr><td>i_uid</td><td>",
             str(inode.i_uid),
             "</td></tr>\n",
             "<tr><td>i_gid</td><td>",
             str(inode.i_gid),
             "</td></tr>\n",
             "<tr><td>i_size</td><td>",
             str(inode.i_size),
             "</td></tr>\n",
             "<tr><td>i_open_time</td><td>",
             time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(inode.i_open_time)),
             "</td></tr>\n",
             "<tr><td>i_creation_time</td><td>",
             time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(inode.i_creation_time)),
             "</td></tr>\n",
             "<tr><td>i_modify_time</td><td>",
             time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(inode.i_modify_time)),
             "</td></tr>\n"]

    for i in range(16):
        graph.append("<tr><td>AP")
        graph.append(str(i))
        graph.append("</td><td port=\"i")
        graph.append(str(i))
        graph.append("\">")
        graph.append(str(inode.i_block[i]))
        graph.append("</td></tr>\n")

    graph.append("<tr><td>i_type</td><td>")
    graph.append(inode.i_type.decode("ascii"))
    graph.append("</td></tr>\n")

    graph.append("<tr><td>i_perm</td><td>")
    graph.append(str(inode.i_perm))
    graph.append("</td></tr>\n")

    graph.append("</table> >];\n")

    for i in range(16):
        if inode.i_block[i] == -1:
            continue
        graph.append("inode")
        graph.append(str(inode_number))
        graph.append(":i")
        graph.append(str(i))
        graph.append(":e -> block")
        graph.append(str(inode.i_block[i]))
        graph.append(":title:w[minlen=2];\n")

        if inode.i_type == b'0':
            graph.append(generate_directory_block_graphviz(fs, inode.i_block[i], i == 0, super_block))
        else:
            graph.append(generate_file_block_graphviz(fs, inode.i_block[i], super_block))

    return "".join(graph)


def generate_file_block_graphviz(fs, block_number, super_block):
    file_block = FileBlock()
    fs.seek(super_block.s_block_start + block_number * struct.calcsize(file_block_binary_format_string),
            io.SEEK_SET)
    read_struct_from_stream(fs, file_block, struct.calcsize(file_block_binary_format_string))

    graph = ["block",
             str(block_number),
             "[label=< <table cellspacing=\"0\" border=\"1\" bgcolor=\"goldenrod1\">\n",
             "<tr><td colspan=\"2\" PORT=\"title\">Bloque Archivo #",
             str(block_number),
             "</td></tr>\n",
             "<tr><td align=\"text\" colspan=\"2\">"]

    for i in range(len(file_block.b_content)):
        if file_block.b_content[i] == 0:
            break

        if file_block.b_content[i] == ord('\n'):
            graph.append("\\\\n")
            graph.append("<br align=\"left\"/>")
        else:
            graph.append(chr(file_block.b_content[i]))

    graph.append("<br align=\"left\"/></td></tr>\n</table> >];\n")
    return "".join(graph)


def generate_directory_block_graphviz(fs, block_number, is_first_block, super_block):
    directory_block = DirectoryBlock()
    fs.seek(super_block.s_block_start + block_number * struct.calcsize(directory_block_binary_format_string), io.SEEK_SET)
    read_struct_from_stream(fs, directory_block, struct.calcsize(directory_block_binary_format_string))

    graph = ["block",
             str(block_number),
             "[label=< <table cellspacing=\"0\" border=\"1\" bgcolor=\"darksalmon\">\n",
             "(<tr><td colspan=\"2\" PORT=\"title\">Bloque Directorio #",
             str(block_number),
             "</td></tr>\n"]

    for i in range(4):
        graph.append("<tr><td>")
        for c in directory_block.b_content[i].b_name:
            if c == 0:
                break
            graph.append(chr(c))
        graph.append("</td><td port=\"i")
        graph.append(str(i))
        graph.append("\">")
        graph.append(str(directory_block.b_content[i].b_inode))
        graph.append("</td></tr>\n")
    graph.append("</table> >];\n")

    index = 2 if is_first_block else 0
    for i in range(index, 4):
        if directory_block.b_content[i].b_inode == -1:
            continue
        graph.append("block")
        graph.append(str(block_number))
        graph.append(":i")
        graph.append(str(i))
        graph.append(":e -> inode")
        graph.append(str(directory_block.b_content[i].b_inode))
        graph.append(":title:w[minlen=2];\n")
        graph.append(generate_inode_graphviz(fs, directory_block.b_content[i].b_inode, super_block))

    return "".join(graph)


def generate_tree_report(disk_id, fs, filepath, first_byte):
    fs.seek(first_byte, 0)
    filesystem_type = struct.unpack("<i", fs.read(4))[0]
    if filesystem_type == 0:
        c_println(f"REP->ERROR->LA PARTICIÓN CON ID {disk_id} NO TIENE UN SISTEMA DE ARCHIVOS")
        return ""

    super_block = SuperBlock()
    fs.seek(first_byte, 0)
    read_struct_from_stream(fs, super_block, struct.calcsize(super_block_binary_format_string))

    main_inode = Inode()
    fs.seek(super_block.s_inode_start + 0 * struct.calcsize(inode_binary_format_string), 0)
    read_struct_from_stream(fs, main_inode, struct.calcsize(inode_binary_format_string))

    graph = "digraph G {\nrankdir=\"LR\";\nnodesep=1.1;\nnode [ shape=none fontname=Helvetica ]\nsplines=polyline;\n"

    graph += generate_inode_graphviz(fs, 0, super_block)
    # graph += generate_bitmap_inode_graphviz(super_block)
    # graph += generate_bitmap_block_graphviz(super_block)
    graph += "}"
    return graph


def generate_bitmap_block_report(fs, part_start):
    super_block = SuperBlock()
    fs.seek(part_start, io.SEEK_SET)
    read_struct_from_stream(fs, super_block, struct.calcsize(super_block_binary_format_string))

    number_of_columns = 20
    bm_block = bytearray(super_block.s_blocks_count)
    fs.seek(super_block.s_bm_block_start, os.SEEK_SET)
    data = fs.read(len(bm_block))
    bm_block[:len(data)] = data

    graph = ["digraph {\n\n  node[ shape=none fontname=Helvetica ]\n\n",
             "  bm_block[ label = <\n<table cellspacing=\"0\" border=\"1\">\n  <tr>\n<td colspan=\"",
             str(number_of_columns + 1),
             "\" bgcolor=\"#238b45\" border=\"0\" width=\"550px\">REPORTE BITMAP BLOQUES</td>\n</tr>\n",
             "<tr>\n<td bgcolor=\"#edf8e9\" width=\"50px\" border=\"0\"></td>\n"]

    for i in range(number_of_columns):
        graph.append("<td bgcolor=\"#74c476\" width=\"50px\" border=\"0\">")
        graph.append(str(i))
        graph.append("</td>\n")

    # last_set_bit = 0
    # for i in range(super_block.s_blocks_count):
    #     if bm_block[i] == 1:
    #         last_set_bit = i
    # Ahora se deben mostrar todos los bits
    last_set_bit = super_block.s_blocks_count - 1

    row = 0
    for i in range(last_set_bit + 1):
        if i % number_of_columns == 0:
            graph.append("</tr><tr><td>")
            graph.append(str(row * number_of_columns))
            row += 1
            graph.append("</td>")
        graph.append("<td bgcolor=\"#")
        graph.append("74c476" if i % 2 == 0 else "edf8e9")
        graph.append("\" width=\"50px\" border=\"0\">")
        graph.append(str(int(bm_block[i])))
        graph.append("</td>\n")

    graph.append("</tr></table>\n  > ]\n}")
    return "".join(graph)


def generate_bitmap_inode_report(fs, part_start):
    super_block = SuperBlock()
    fs.seek(part_start, io.SEEK_SET)
    read_struct_from_stream(fs, super_block, struct.calcsize(super_block_binary_format_string))

    number_of_columns = 20

    bm_inode = bytearray(super_block.s_inodes_count)
    fs.seek(super_block.s_bm_inode_start, os.SEEK_SET)
    data = fs.read(len(bm_inode))
    bm_inode[:len(data)] = data

    graph = ["digraph {\n\n  node[ shape=none fontname=Helvetica ]\n\n",
             "  bm_inode[ label = <\n<table cellspacing=\"0\" border=\"1\">\n  <tr>\n<td colspan=\"",
             str(number_of_columns + 1),
             "\" bgcolor=\"#238b45\" border=\"0\" width=\"550px\">REPORTE BITMAP INODOS</td>\n</tr>\n",
             "<tr>\n<td bgcolor=\"#edf8e9\" width=\"50px\" border=\"0\"></td>\n"]

    for i in range(number_of_columns):
        graph.append("<td bgcolor=\"#74c476\" width=\"50px\" border=\"0\">")
        graph.append(str(i))
        graph.append("</td>\n")

    # last_set_bit = 0
    # for i in range(super_block.s_inodes_count):
    #     if bm_inode[i] == 1:
    #         last_set_bit = i
    # Ahora se deben mostrar todos los bits
    last_set_bit = super_block.s_inodes_count - 1

    row = 0
    for i in range(last_set_bit + 1):
        if i % number_of_columns == 0:
            graph.append("</tr><tr><td>")
            graph.append(str(row * number_of_columns))
            row += 1
            graph.append("</td>")
        graph.append("<td bgcolor=\"#")
        graph.append("74c476" if i % 2 == 0 else "edf8e9")
        graph.append("\" width=\"50px\" border=\"0\">")
        graph.append(str(int(bm_inode[i])))
        graph.append("</td>\n")

    graph.append("</tr></table>\n  > ]\n}")
    return "".join(graph)


def generate_disk_report_ebr(fs, mbr: MBR, p_index):
    partition: Partition = mbr.mbr_partitions[p_index]

    ebr = EBR()
    fs.seek(partition.part_start)
    read_struct_from_stream(fs, ebr, struct.calcsize(ebr_binary_format_string))

    # Extended Disc overall
    graph = ["<td><table><tr>\n",
             "<td bgcolor=\"aquamarine4\" width=\"150.5px\">",
             partition.part_name.decode('utf-8').rstrip('\x00'),
             "<br/>", str(partition.part_s),
             "bytes<br/>",
             "{:.3f}".format(partition.part_s * 100 / mbr.mbr_size).rstrip("0").rstrip("."), "% del disco </td>\n",
             "<td bgcolor=\"aquamarine\" width=\"150.5px\">EBR<br/>",
             "{:.3f}".format(struct.calcsize(ebr_binary_format_string) * 100 / mbr.mbr_size).rstrip("0").rstrip("."),
             "% del disco </td>\n"]

    # First EBR
    space1 = 0
    if ebr.part_status == b'F':
        space1 = partition.part_s - struct.calcsize(ebr_binary_format_string)
        if space1 != 0:
            graph.append("<td bgcolor=\"lightgray\" width=\"")
            graph.append("{:.3f}".format(space1 * 100 * pixel_constant / mbr.mbr_size).rstrip("0").rstrip("."))
            graph.append("px\">free<br/>")
            graph.append(str(space1))
            graph.append("bytes<br/>")
            graph.append("{:.3f}".format(space1 * 100 / mbr.mbr_size).rstrip("0").rstrip("."))
            graph.append("% del disco </td>\n")
        graph.append("</tr>\n</table></td>\n")
        return "".join(graph)

    # First Logic
    space1 = ebr.part_s

    graph.append("<td bgcolor=\"orange\" width=\"")
    graph.append("{:.3f}".format(space1 * pixel_constant * 100 / mbr.mbr_size).rstrip("0").rstrip("."))
    graph.append("px\">")
    graph.append(ebr.part_name.decode("utf-8").rstrip(chr(0)))
    graph.append("<br/>")
    graph.append(str(space1))
    graph.append(" bytes <br/>")
    graph.append("{:.3f}".format(space1 * 100 / mbr.mbr_size).rstrip("0").rstrip("."))
    graph.append("% del disco </td>\n")

    if ebr.part_next == 0:
        space1 = partition.part_s - (struct.calcsize(ebr_binary_format_string) + ebr.part_s)
        if space1 != 0:
            graph.append("<td bgcolor=\"lightgray\" width=\"")
            graph.append("{:.3f}".format(space1 * pixel_constant * 100 / mbr.mbr_size).rstrip("0").rstrip("."))
            graph.append("px\">free<br/>")
            graph.append(str(space1))
            graph.append("bytes<br/>")
            graph.append("{:.3f}".format(space1 * 100 / mbr.mbr_size).rstrip("0").rstrip("."))
            graph.append("% del disco </td>\n")
        graph.append("</tr>\n</table></td>\n")
        return ''.join(graph)

    last_start = 0
    before_last = ebr
    last = ebr

    while last.part_next != 0:
        # Actualizar el ultimo
        last_start = last.part_next
        fs.seek(last.part_next, io.SEEK_SET)
        read_struct_from_stream(fs, last, struct.calcsize(ebr_binary_format_string))

        # # Espacio entre el ultimo y este
        # space1 = last_start - (before_last.part_start + before_last.part_s)
        # if space1 != 0:
        #     graph.append("<td bgcolor=\"lightgray\" width=\"")
        #     graph.append("{:.3f}".format(space1 * pixel_constant * 100 / mbr.mbr_size).rstrip("0").rstrip("."))
        #     graph.append("px\">free<br/>")
        #     graph.append(str(space1))
        #     graph.append("bytes<br/>")
        #     graph.append("{:.3f}".format(space1 * 100 / mbr.mbr_size).rstrip("0").rstrip("."))
        #     graph.append("% del disco </td>\n")

        # EBR y esta logica
        graph.append("<td bgcolor=\"aquamarine\" width=\"150.5px\">EBR<br/>")
        graph.append("{:.3f}".format(struct.calcsize(ebr_binary_format_string) * 100 / mbr.mbr_size).rstrip("0").rstrip("."))
        graph.append("% del disco </td>\n")

        space1 = last.part_s
        graph.append("<td bgcolor=\"orange\" width=\"")
        graph.append("{:.3f}".format(space1 * pixel_constant * 100 / mbr.mbr_size).rstrip("0").rstrip("."))
        graph.append("px\">")
        graph.append(last.part_name.decode("utf-8").rstrip(chr(0)))
        graph.append("<br/>")
        graph.append(str(space1))
        graph.append(" bytes<br/>")
        graph.append("{:.3f}".format(space1 * 100 / mbr.mbr_size).rstrip("0").rstrip("."))
        graph.append("% del disco </td>\n")

        # Actualizar antes del siguiente ciclo
        before_last = last

    # Espacio entre el ultimo y este
    space1 = (partition.part_start + partition.part_s) - (last.part_start + last.part_s)
    if space1 != 0:
        graph.append("<td bgcolor=\"lightgray\" width=\"")
        graph.append("{:.3f}".format(space1 * pixel_constant * 100 / mbr.mbr_size).rstrip("0").rstrip("."))
        graph.append("px\">free<br/>")
        graph.append(str(space1))
        graph.append("bytes<br/>")
        graph.append("{:.3f}".format(space1 * 100 / mbr.mbr_size).rstrip("0").rstrip("."))
        graph.append("% del disco </td>\n")

    graph.append("</tr>\n</table></td>\n")
    return "".join(graph)


def generate_disk_report(fs):
    mbr: MBR = MBR()
    fs.seek(0, io.SEEK_SET)
    read_struct_from_stream(fs, mbr, struct.calcsize(mbr_binary_format_string))

    graph = ["digraph {\n\n  node [ shape=none fontname=Helvetica ]\n\n  n1 [ label = <\n<table>\n  <tr>\n"]

    while True:
        graph.append("<td bgcolor=\"yellow\" width=\"")
        graph.append(str(int(struct.calcsize(mbr_binary_format_string) * 100 * pixel_constant / mbr.mbr_size)))
        graph.append("px\">MBR<br/>")
        graph.append(str(struct.calcsize(mbr_binary_format_string)))
        graph.append("bytes<br/>")
        graph.append("{:.3f}".format(struct.calcsize(mbr_binary_format_string) * 100 / mbr.mbr_size).rstrip("0").rstrip("."))
        graph.append("% del disco </td>\n")

        # Caso de ninguna partición
        if mbr.mbr_partitions[0].part_status == b'F':
            graph.append(" <td bgcolor=\"lightgray\" width=\"150.5px\">free<br/>")
            graph.append(str(int(mbr.mbr_size - struct.calcsize(mbr_binary_format_string))))
            graph.append("bytes<br/>")
            graph.append("{:.3f}".format(float(mbr.mbr_size - struct.calcsize(mbr_binary_format_string)) * 100 / mbr.mbr_size).rstrip("0").rstrip("."))
            graph.append("% del disco </td>\n")
            break

        # Espacio libre entre borde Izquierdo<->Partición0
        space1 = mbr.mbr_partitions[0].part_start - struct.calcsize(mbr_binary_format_string)
        if space1 != 0:
            graph.append(" <td bgcolor=\"lightgray\" width=")
            graph.append(str(int(space1 * 100 * pixel_constant / mbr.mbr_size)))
            graph.append("px\">free<br/>")
            graph.append(str(space1))
            graph.append("bytes<br/>")
            graph.append("{:.3f}".format(space1 * 100 / mbr.mbr_size).rstrip("0").rstrip("."))
            graph.append("% del disco </td>\n")

        # Partición0
        space1 = mbr.mbr_partitions[0].part_s
        if mbr.mbr_partitions[0].part_type == b'E':
            graph.append(generate_disk_report_ebr(fs, mbr, 0))
        else:
            graph.append("<td bgcolor=\"darkgreen\" width=\"")
            graph.append(str(int(space1 * 100 * pixel_constant / mbr.mbr_size)))
            graph.append("px\">")
            graph.append(mbr.mbr_partitions[0].part_name.rstrip(b'\x00').decode("utf-8"))
            graph.append("<br/>")
            graph.append(str(space1))
            graph.append("bytes<br/>")
            graph.append("{:.3f}".format(space1 * 100 / mbr.mbr_size).rstrip("0").rstrip("."))
            graph.append("% del disco </td>\n")

        ########################

        # Partición0 - Borde Derecho
        if mbr.mbr_partitions[1].part_status == b'F':
            space1 = mbr.mbr_size - (mbr.mbr_partitions[0].part_start + mbr.mbr_partitions[0].part_s)
            graph.append("<td bgcolor=\"lightgray\" width=\"")
            graph.append(str(int(space1 * 100 * pixel_constant / mbr.mbr_size)))
            graph.append("px\">free<br/>")
            graph.append(str(space1))
            graph.append("bytes<br/>")
            graph.append("{:.3f}".format(space1 * 100 / mbr.mbr_size).rstrip("0").rstrip("."))
            graph.append("% del disco </td>\n")
            break

        # Espacio libre Partición0<->Partición1
        space1 = mbr.mbr_partitions[1].part_start - (mbr.mbr_partitions[0].part_start + mbr.mbr_partitions[0].part_s)
        if space1 != 0:
            graph.append(" <td bgcolor=\"lightgray\" width=")
            graph.append(str(int(space1 * 100 * pixel_constant / mbr.mbr_size)))
            graph.append("px\">free<br/>")
            graph.append(str(space1))
            graph.append("bytes<br/>")
            graph.append("{:.3f}".format(space1 * 100 / mbr.mbr_size).rstrip("0").rstrip("."))
            graph.append("% del disco </td>\n")

        # Parte 1
        space1 = mbr.mbr_partitions[1].part_s
        if mbr.mbr_partitions[1].part_type == b'E':
            graph.append(generate_disk_report_ebr(fs, mbr, 1))
        else:
            graph.append("<td bgcolor=\"darkgreen\" width=\"")
            graph.append(str(int(space1 * 100 * pixel_constant / mbr.mbr_size)))
            graph.append("px\">")
            graph.append(mbr.mbr_partitions[1].part_name.rstrip(b'\x00').decode("utf-8"))
            graph.append("<br/>")
            graph.append(str(space1))
            graph.append("bytes<br/>")
            graph.append("{:.3f}".format(space1 * 100 / mbr.mbr_size).rstrip("0").rstrip("."))
            graph.append("% del disco </td>\n")

        ################################
        # Partición1-BordeDerecho

        if mbr.mbr_partitions[2].part_status == b'F':
            space1 = mbr.mbr_size - (mbr.mbr_partitions[1].part_start + mbr.mbr_partitions[1].part_s)
            graph.append("<td bgcolor=\"lightgray\" width=\"")
            graph.append(str(int(space1 * 100 * pixel_constant / mbr.mbr_size)))
            graph.append("px\">free<br/>")
            graph.append(str(space1))
            graph.append("bytes<br/>")
            "{:.3f}".format(space1 * 100 / mbr.mbr_size).rstrip("0").rstrip(".")
            graph.append("% del disco </td>\n")
            break

        # Espacio libre Partición1<->Partición2
        space1 = mbr.mbr_partitions[2].part_start - (mbr.mbr_partitions[1].part_start + mbr.mbr_partitions[1].part_s)
        if space1 != 0:
            graph.append(" <td bgcolor=\"lightgray\" width=")
            graph.append(str(int(space1 * 100 * pixel_constant / mbr.mbr_size)))
            graph.append("px\">free<br/>")
            graph.append(str(space1))
            graph.append("bytes<br/>")
            graph.append("{:.3f}".format(space1 * 100 / mbr.mbr_size).rstrip("0").rstrip("."))
            graph.append("% del disco </td>\n")

        # Partición2
        space1 = mbr.mbr_partitions[2].part_s
        if mbr.mbr_partitions[2].part_type == b'E':
            graph.append(generate_disk_report_ebr(fs, mbr, 2))
        else:
            graph.append("<td bgcolor=\"darkgreen\" width=\"")
            graph.append(str(int(space1 * 100 * pixel_constant / mbr.mbr_size)))
            graph.append("px\">")
            graph.append(mbr.mbr_partitions[2].part_name.rstrip(b'\x00').decode("utf-8"))
            graph.append("<br/>")
            graph.append(str(space1))
            graph.append("bytes<br/>")
            graph.append("{:.3f}".format(space1 * 100 / mbr.mbr_size).rstrip("0").rstrip("."))
            graph.append("% del disco </td>\n")

            pass
        # Partición2<->BordeDerecho
        if mbr.mbr_partitions[3].part_status == b'F':
            space1 = mbr.mbr_size - (mbr.mbr_partitions[2].part_start + mbr.mbr_partitions[2].part_s)
            graph.append("<td bgcolor=\"lightgray\" width=\"")
            graph.append(str(int(space1 * 100 * pixel_constant / mbr.mbr_size)))
            graph.append("px\">free<br/>")
            graph.append(str(space1))
            graph.append("bytes<br/>")
            graph.append("{:.3f}".format(space1 * 100 / mbr.mbr_size).rstrip("0").rstrip("."))
            graph.append("% del disco </td>\n")
            break

        # Espacio libre Partición2<->Partición3
        space1 = mbr.mbr_partitions[3].part_start - (mbr.mbr_partitions[2].part_start + mbr.mbr_partitions[2].part_s)
        if space1 != 0:
            graph.append(" <td bgcolor=\"lightgray\" width=")
            graph.append(str(int(space1 * 100 * pixel_constant / mbr.mbr_size)))
            graph.append("px\">free<br/>")
            graph.append(str(int(space1)))
            graph.append("bytes<br/>")
            graph.append("{:.3f}".format(space1 * 100 / mbr.mbr_size).rstrip("0").rstrip("."))
            graph.append("% del disco </td>\n")

        # Partición3
        space1 = mbr.mbr_partitions[3].part_s
        if mbr.mbr_partitions[3].part_type == b'E':
            graph.append(generate_disk_report_ebr(fs, mbr, 3))
        else:
            graph.append("<td bgcolor=\"darkgreen\" width=\"")
            graph.append(str(int(space1 * 100 * pixel_constant / mbr.mbr_size)))
            graph.append("px\">")
            graph.append(str(mbr.mbr_partitions[3].part_name.decode('utf-8').rstrip('\x00')))
            graph.append("<br/>")
            graph.append(str(space1))
            graph.append("bytes<br/>")
            graph.append("{:.3f}".format(space1 * 100 / mbr.mbr_size).rstrip("0").rstrip("."))
            graph.append("% del disco </td>\n")

        # Partición3<->BordeDerecho
        space1 = mbr.mbr_size - (mbr.mbr_partitions[3].part_start + mbr.mbr_partitions[3].part_s)
        if space1 != 0:
            graph.append(" <td bgcolor=\"lightgray\" width=\"")
            graph.append(str(int(space1 * 100 * pixel_constant / mbr.mbr_size)))
            graph.append("px\">free<br/>")
            graph.append(str(int(space1)))
            graph.append("bytes<br/>")
            graph.append("{:.3f}".format(space1 * 100 / mbr.mbr_size).rstrip("0").rstrip("."))
            graph.append("% del disco </td>\n")
        break
    graph.append("</tr>\n</table>\n  > ]\n}")
    return "".join(graph)


def generate_super_block_report(disk_id, fs, filepath, first_byte):
    fs.seek(first_byte)
    filesystem_type = struct.unpack('>i', fs.read(4))[0]

    if filesystem_type == 0:
        c_println(f"REP->ERROR->LA PARTICIÓN CON ID {disk_id} NO TIENE UN SISTEMA DE ARCHIVOS")
        return ""

    super_block = SuperBlock()
    fs.seek(first_byte)
    read_struct_from_stream(fs, super_block, struct.calcsize(super_block_binary_format_string))

    graph = []
    graph.append("digraph {\n\n  node [ shape=none fontname=Helvetica ]\n\n")
    graph.append("  n1 [ label = <\n<table cellspacing=\"0\" border=\"1\">\n  <tr>\n")
    graph.append("<td colspan=\"2\" bgcolor=\"#238b45\" border=\"0\" width=\"300px\">REPORTE SUPERBLOQUE ")
    graph.append(disk_id)
    graph.append("</td>\n</tr>\n")

    graph.append("<tr>\n<td bgcolor=\"#74c476\" border=\"0\">sb_nombre_hd</td>\n")
    graph.append("<td bgcolor=\"#74c476\" border=\"0\" align=\"left\">")
    graph.append(get_filename_by_filepath(filepath, True))
    graph.append("</td>\n</tr>\n")

    graph.append("<tr>\n<td bgcolor=\"#edf8e9\" border=\"0\">s_filesystem_type</td>\n")
    graph.append("<td bgcolor=\"#edf8e9\" border=\"0\" align=\"left\">")
    graph.append("EXT2")
    graph.append("</td>\n</tr>\n")

    graph.append("<tr>\n<td bgcolor=\"#74c476\" border=\"0\">s_inodes_count</td>\n")
    graph.append('<td bgcolor="#74c476" border="0" align="left">')
    graph.append(str(super_block.s_inodes_count))
    graph.append("</td>\n</tr>\n")

    graph.append("<tr>\n<td bgcolor=\"#edf8e9\" border=\"0\">s_blocks_count</td>\n")
    graph.append('<td bgcolor="#edf8e9" border="0" align="left">')
    graph.append(str(super_block.s_blocks_count))
    graph.append("</td>\n</tr>\n")

    graph.append("<tr>\n<td bgcolor=\"#74c476\" border=\"0\">s_free_inodes_count</td>\n")
    graph.append('<td bgcolor="#74c476" border="0" align="left">')
    graph.append(str(super_block.s_free_inodes_count))
    graph.append("</td>\n</tr>\n")

    graph.append("<tr>\n<td bgcolor=\"#edf8e9\" border=\"0\">s_free_blocks_count</td>\n")
    graph.append('<td bgcolor="#edf8e9" border="0" align="left">')
    graph.append(str(super_block.s_free_blocks_count))
    graph.append("</td>\n</tr>\n")

    graph.append("<tr>\n<td bgcolor=\"#74c476\" border=\"0\">s_mount_time</td>\n")
    graph.append('<td bgcolor="#74c476" border="0" align="left">')
    graph.append(time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(super_block.s_mount_time)))
    graph.append("</td>\n</tr>\n")

    graph.append("<tr>\n<td bgcolor=\"#edf8e9\" border=\"0\">s_unmount_time</td>\n")
    graph.append('<td bgcolor="#edf8e9" border="0" align="left">')
    graph.append(time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(super_block.s_unmount_time)))
    graph.append("</td>\n</tr>\n")

    graph.append("<tr>\n<td bgcolor=\"#74c476\" border=\"0\">s_mnt_count</td>\n")
    graph.append('<td bgcolor="#74c476" border="0" align="left">')
    graph.append(str(super_block.s_mnt_count))
    graph.append("</td>\n</tr>\n")

    graph.append("<tr>\n<td bgcolor=\"#edf8e9\" border=\"0\" >s_magic</td>\n")
    graph.append('<td bgcolor="#edf8e9" border="0" align="left">')
    graph.append("0x%X" % super_block.s_magic)
    graph.append("</td>\n</tr>\n")

    graph.append("<tr>\n<td bgcolor=\"#74c476\" border=\"0\" >s_inode_size</td>\n")
    graph.append('<td bgcolor="#74c476" border="0" align="left">')
    graph.append(str(super_block.s_inode_size))
    graph.append("</td>\n</tr>\n")

    graph.append("<tr>\n<td bgcolor=\"#edf8e9\" border=\"0\">s_block_size</td>\n")
    graph.append('<td bgcolor="#edf8e9" border="0" align="left">')
    graph.append(str(super_block.s_block_size))
    graph.append("</td>\n</tr>\n")

    graph.append("<tr>\n<td bgcolor=\"#74c476\" border=\"0\">s_inode_start</td>\n")
    graph.append("<td bgcolor=\"#74c476\" border=\"0\" align=\"left\">")
    graph.append(str(super_block.s_inode_start))
    graph.append("</td>\n</tr>\n")

    graph.append("<tr>\n<td bgcolor=\"#edf8e9\" border=\"0\">s_block_start</td>\n")
    graph.append("<td bgcolor=\"#edf8e9\" border=\"0\" align=\"left\">")
    graph.append(str(super_block.s_block_start))
    graph.append("</td>\n</tr>\n")

    graph.append("<tr>\n<td bgcolor=\"#74c476\" border=\"0\">s_first_inode</td>\n")
    graph.append("<td bgcolor=\"#74c476\" border=\"0\" align=\"left\">")
    graph.append(str(super_block.s_first_inode))
    graph.append("</td>\n</tr>\n")

    graph.append("<tr>\n<td bgcolor=\"#edf8e9\" border=\"0\">s_first_block</td>\n")
    graph.append("<td bgcolor=\"#edf8e9\" border=\"0\" align=\"left\">")
    graph.append(str(super_block.s_first_block))
    graph.append("</td>\n</tr>\n")

    graph.append("<tr>\n<td bgcolor=\"#74c476\" border=\"0\">s_bm_inode_start</td>\n")
    graph.append("<td bgcolor=\"#74c476\" border=\"0\" align=\"left\">")
    graph.append(str(super_block.s_bm_inode_start))
    graph.append("</td>\n</tr>\n")

    graph.append("<tr>\n<td bgcolor=\"#edf8e9\" border=\"0\">s_bm_block_start</td>\n")
    graph.append("<td bgcolor=\"#edf8e9\" border=\"0\" align=\"left\">")
    graph.append(str(super_block.s_bm_block_start))
    graph.append("</td>\n</tr>\n")

    graph.append("<tr>\n<td bgcolor=\"#74c476\" border=\"0\">s_inode_start</td>\n")
    graph.append("<td bgcolor=\"#74c476\" border=\"0\" align=\"left\">")
    graph.append(str(super_block.s_inode_start))
    graph.append("</td>\n</tr>\n")

    graph.append("<tr>\n<td bgcolor=\"#edf8e9\" border=\"0\">s_block_start</td>\n")
    graph.append("<td bgcolor=\"#edf8e9\" border=\"0\" align=\"left\">")
    graph.append(str(super_block.s_block_start))
    graph.append("</td>\n</tr>\n")

    graph.append("</table>\n  > ]\n}")
    return ''.join(graph)


def generate_mbr_report(filepath):
    mbr = MBR()
    with open(filepath, 'rb') as fs:
        fs.seek(0, os.SEEK_SET)
        read_struct_from_stream(fs, mbr, struct.calcsize(mbr_binary_format_string))

    graph = f"""
        digraph {{
          node [ shape=none fontname=Helvetica ]
        
          n1 [ label = <
          <table cellspacing="0" border="1">
            <tr>
              <td colspan="2" bgcolor="#810f7c" border="0" width="300px">REPORTE MBR</td>
            </tr>
            <tr>
              <td bgcolor="#C9B5DF" border="0">mbr_size</td>
              <td bgcolor="#C9B5DF" border="0" align="left">{mbr.mbr_size}</td>
            </tr>
            <tr>
              <td bgcolor="#F7FCFD" border="0">mbr_creation_date</td>
              <td bgcolor="#F7FCFD" border="0" align="left">{time.strftime("%a, %d-%m-%Y %H:%M:%S", time.localtime(mbr.mbr_creation_date))}</td>
            </tr>
            <tr>
              <td bgcolor="#C9B5DF" border="0">mbr_dsk_signature</td>
              <td bgcolor="#C9B5DF" border="0" align="left">{mbr.mbr_dsk_signature}</td>
            </tr>
            <tr>
              <td bgcolor="#F7FCFD" border="0">mbr_dsk_fit</td>
              <td bgcolor="#F7FCFD" border="0" align="left">{mbr.dsk_fit.decode("ascii")}</td>
            </tr>
        """

    for partition in mbr.mbr_partitions:
        graph += f"""
            <tr>
              <td colspan="2" bgcolor="#810f7c" border="0">Particion</td>
            </tr>
            <tr>
              <td bgcolor="#C9B5DF" border="0">part_status</td>
              <td bgcolor="#C9B5DF" border="0" align="left">{partition.part_status.decode('ascii')}</td>
            </tr>
            <tr>
              <td bgcolor="#F7FCFD" border="0">part_type</td>
              <td bgcolor="#F7FCFD" border="0" align="left">{partition.part_type.decode('ascii')}</td>
            </tr>
            <tr>
              <td bgcolor="#C9B5DF" border="0">part_fit</td>
              <td bgcolor="#C9B5DF" border="0" align="left">{partition.part_fit.decode('ascii')}</td>
            </tr>
            <tr>
              <td bgcolor="#F7FCFD" border="0">part_start</td>
              <td bgcolor="#F7FCFD" border="0" align="left">{partition.part_start}</td>
            </tr>
            <tr>
              <td bgcolor="#C9B5DF" border="0">part_size</td>
              <td bgcolor="#C9B5DF" border="0" align="left">{partition.part_s}</td>
            </tr>
            <tr>
              <td bgcolor="#F7FCFD" border="0">part_name</td>
              <td bgcolor="#F7FCFD" border="0" align="left">{partition.part_name.decode("utf-8").rstrip(chr(0))}</td>
            </tr>
        """

        if partition.part_type == b'E':
            graph += make_mbr_report_ebr(filepath, partition.part_start)

    graph += "</table>\n  > ]\n}"
    return graph


def make_mbr_report_ebr(filepath, start_byte):
    with open(filepath, 'rb') as fs:
        ebr = EBR()
        fs.seek(start_byte)
        read_struct_from_stream(fs, ebr, struct.calcsize(ebr_binary_format_string))

        if ebr.part_status == 'F':
            return ""

        graph = f"""
            <tr>
            <td colspan="2" bgcolor="#D94801" border="0">Particion Logica</td>
            </tr>
            <tr>
            <td bgcolor="#FEF9F5" border="0">part_status</td>
            <td bgcolor="#FEF9F5" border="0" align="left">{ebr.part_status.decode('ascii')}</td>
            </tr>
            <tr>
            <td bgcolor="#FDD0A2" border="0">part_next</td>
            <td bgcolor="#FDD0A2" border="0" align="left">{ebr.part_next}</td>
            </tr>
            <tr>
            <td bgcolor="#FEF9F5" border="0">part_fit</td>
            <td bgcolor="#FEF9F5" border="0" align="left">{ebr.part_fit.decode("ascii")}</td>
            </tr>
            <tr>
            <td bgcolor="#FDD0A2" border="0">part_start</td>
            <td bgcolor="#FDD0A2" border="0" align="left">{ebr.part_start}</td>
            </tr>
            <tr>
            <td bgcolor="#FEF9F5" border="0">part_size</td>
            <td bgcolor="#FEF9F5" border="0" align="left">{ebr.part_s}</td>
            </tr>
            <tr>
            <td bgcolor="#FDD0A2" border="0">part_name</td>
            <td bgcolor="#FDD0A2" border="0" align="left">{ebr.part_name.decode("ascii").rstrip(chr(0))}</td>
            </tr>
        """

        while ebr.part_next != 0:
            fs.seek(ebr.part_next)
            read_struct_from_stream(fs, ebr, struct.calcsize(ebr_binary_format_string))

            graph += f"""
                <tr>
                <td colspan="2" bgcolor="#D94801" border="0">Particion Logica</td>
                </tr>
                <tr>
                <td bgcolor="#FEF9F5" border="0">part_status</td>
                <td bgcolor="#FEF9F5" border="0" align="left">{ebr.part_status.decode('ascii')}</td>
                </tr>
                <tr>
                <td bgcolor="#FDD0A2" border="0">part_next</td>
                <td bgcolor="#FDD0A2" border="0" align="left">{ebr.part_next}</td>
                </tr>
                <tr>
                <td bgcolor="#FEF9F5" border="0">part_fit</td>
                <td bgcolor="#FEF9F5" border="0" align="left">{ebr.part_fit.decode('ascii')}</td>
                </tr>
                <tr>
                <td bgcolor="#FDD0A2" border="0">part_start</td>
                <td bgcolor="#FDD0A2" border="0" align="left">{ebr.part_start}</td>
                </tr>
                <tr>
                <td bgcolor="#FEF9F5" border="0">part_size</td>
                <td bgcolor="#FEF9F5" border="0" align="left">{ebr.part_s}</td>
                </tr>
                <tr>
                <td bgcolor="#FDD0A2" border="0">part_name</td>
                <td bgcolor="#FDD0A2" border="0" align="left">{ebr.part_name.decode('ascii').rstrip(chr(0))}</td>
                </tr>
            """

    return graph


def generate_file_report(disk_id, fs, first_byte, inner_file_path):
    fs.seek(first_byte)
    filesystem_type = struct.unpack("<i", fs.read(4))[0]

    # Check if the file system type is 0
    if filesystem_type == 0:
        c_println(f"REP->ERROR->LA PARTICIÓN CON ID {disk_id} NO TIENE UN SISTEMA DE ARCHIVOS")
        return ""

    super_block = SuperBlock()
    fs.seek(first_byte)
    read_struct_from_stream(fs, super_block, struct.calcsize(super_block_binary_format_string))

    file_inode_number = get_element_inode_number(fs, super_block, 0, decompose_file_path(inner_file_path), 1)

    if file_inode_number < 0:
        c_println(f"REP->ERROR-> EL ARCHIVO <{inner_file_path} NO EXISTE")
        return ""

    return get_file_content(fs, super_block, file_inode_number)
