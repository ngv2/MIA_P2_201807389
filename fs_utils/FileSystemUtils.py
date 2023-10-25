import io
import os
import re
import time
import struct


from structs.FileBlock import FileBlock, file_block_binary_format_string
from structs.SuperBlock import SuperBlock, super_block_binary_format_string
from utils.Utils import write_struct_to_stream, read_struct_from_stream
from general.LoggedUser import LoggedUser
from structs.DirectoryBlock import DirectoryBlock, directory_block_binary_format_string
from structs.Inode import Inode, inode_binary_format_string
from structs.Content import Content
from structs.Permissions import Permissions
from structs.DirectoryElement import DirectoryElement

from typing import BinaryIO


def make_file(disk_path, super_block, filename, next_free_inode, fs_start, directory_block,
              directory_block_number, dir_block_free_slot_index, fs):
    if next_free_inode == -1:
        print("FILESYSTEM->ERROR-> NO QUEDAN INODOS DISPONIBLES")
        return -1

    set_inode_usage(fs, fs_start, next_free_inode, 1)

    directory_block.b_content[dir_block_free_slot_index].b_name[:len(filename)] = filename.encode('ascii')
    directory_block.b_content[dir_block_free_slot_index].b_inode = next_free_inode

    fs.seek(super_block.s_block_start + directory_block_number * struct.calcsize(directory_block_binary_format_string))
    write_struct_to_stream(fs, directory_block)

    new_file_inode = Inode(
        i_uid=LoggedUser.uid,
        i_gid=LoggedUser.gid,
        i_size=struct.calcsize(inode_binary_format_string),
        i_open_time=int(time.time()),
        i_creation_time=int(time.time()),
        i_modify_time=int(time.time()),
        i_block=[-1] * 16,
        i_type=b'1',
        i_perm=644
    )

    fs.seek(super_block.s_inode_start + next_free_inode * struct.calcsize(inode_binary_format_string))
    write_struct_to_stream(fs, new_file_inode)

    return 0


def make_single_directory(disk_path, super_block, current_inode_number, directories, next_free_inode, next_free_block,
                          fs_start, directory_block, i, j, prev_block_number, fs, father_folder_name):
    if next_free_inode == -1:
        print("FILESYSTEM->ERROR-> NO QUEDAN INODOS DISPONIBLES")
        return -1

    if next_free_block == -1:
        print("FILESYSTEM->ERROR-> NO QUEDAN BLOQUES DISPONIBLES")
        return -2

    set_inode_usage(fs, fs_start, next_free_inode, 1)
    set_block_usage(fs, fs_start, next_free_block, 1)

    directory_block.b_content[j].b_name[:] = struct.pack("12s", directories[0].encode('ascii'))
    directory_block.b_content[j].b_inode = next_free_inode

    fs.seek(super_block.s_block_start + prev_block_number * struct.calcsize(directory_block_binary_format_string))
    write_struct_to_stream(fs, directory_block)

    new_dir_inode = Inode(LoggedUser.uid,
                          LoggedUser.gid,
                          struct.calcsize(inode_binary_format_string),
                          int(time.time()),
                          int(time.time()),
                          int(time.time()),
                          [next_free_block] + ([-1] * 15),
                          b'0',
                          644
                          )

    fs.seek(super_block.s_inode_start + next_free_inode * struct.calcsize(inode_binary_format_string))
    write_struct_to_stream(fs, new_dir_inode)

    new_dir_block = DirectoryBlock([
        Content(b_name=[c.encode('ascii') for c in father_folder_name], b_inode=current_inode_number),
        Content(b_name=[ord(c) for c in directories[0]], b_inode=next_free_inode), # Content puede tomar una lista y la pasa a bytearray
        Content(b_name=struct.pack("12s", "-".encode('ascii')), b_inode=-1),
        Content(b_name=struct.pack("12s", "-".encode('ascii')), b_inode=-1)
    ])

    fs.seek(super_block.s_block_start + next_free_block * struct.calcsize(directory_block_binary_format_string))
    write_struct_to_stream(fs, new_dir_block)

    return 0


# noinspection DuplicatedCode
def get_element_father_block_number(fs, super_block, current_inode_number, directories, element_type):
    main_inode = Inode()
    fs.seek(super_block.s_inode_start + current_inode_number * struct.calcsize(inode_binary_format_string))
    read_struct_from_stream(fs, main_inode, struct.calcsize(inode_binary_format_string))

    if element_type == 0 and main_inode.i_type == b'1':
        print("FILESYSTEM->ERROR-> <" + directories[0] + "> es un archivo, no un directorio")
        return -2

    for i in range(16):
        if main_inode.i_block[i] == -1:
            continue

        index = 0
        if i == 0:
            index = 2

        directory_block = DirectoryBlock()
        fs.seek(super_block.s_block_start + main_inode.i_block[i] * struct.calcsize(directory_block_binary_format_string))
        read_struct_from_stream(fs, directory_block, struct.calcsize(directory_block_binary_format_string))

        for j in range(index):
            if directory_block.b_content[j].b_inode == -1:
                continue

            if directory_block.b_content[j].b_name.decode('utf-8').rstrip('\x00') == directories[0]:
                sus_node = Inode()
                fs.seek(super_block.s_inode_start + directory_block.b_content[j].b_inode * struct.calcsize(inode_binary_format_string))
                read_struct_from_stream(fs, sus_node, struct.calcsize(inode_binary_format_string))

                # Archivo tratado como directorio
                if element_type == 0 and sus_node.i_type == b'1':
                    print("FILESYSTEM->ERROR-> <" + directories[0] + "> es un archivo, no un directorio")
                    return -2

                if len(directories) == 1:
                    # Directorio tratado como un archivo
                    if element_type == 1 and sus_node.i_type == b'0':
                        print("FILESYSTEM->ERROR-> <" + directories[0] + "> es un directorio, no un archivo")
                        return -2
                    return main_inode.i_block[i]

                new_dirs = directories[1:]
                return get_element_father_block_number(fs, super_block, directory_block.b_content[j].b_inode, new_dirs, element_type)

    return -1


def make_directories(disk_path, super_block, current_inode_number, directories):
    if len(directories) == 0:
        return 0

    fs = open(disk_path, 'rb+')
    existing_dir_inode = get_element_inode_number(fs, super_block, current_inode_number, directories[:1], 0)

    # Si el siguiente directorio ya existe, saltar la creación del mismo y seguir con los demás
    if existing_dir_inode != -1:
        new_dirs = directories[1:]
        return make_directories(disk_path, super_block, existing_dir_inode, new_dirs)

    # El directorio no existe, hay que crearlo
    fs_start = super_block.s_bm_inode_start - struct.calcsize(super_block_binary_format_string)

    current_inode = Inode()
    fs.seek(super_block.s_inode_start + current_inode_number * struct.calcsize(inode_binary_format_string))
    read_struct_from_stream(fs, current_inode, struct.calcsize(inode_binary_format_string))

    # Tipo equivocado
    if current_inode.i_type == b'1':
        print("FILESYSTEM->ERROR-> <", directories[0], "> es un archivo, no un directorio")
        return 2

    father_folder_name = "padre_desc"
    for i in range(16):
        # Si el siguiente puntero esta vacío, primero hay que crearle el bloque extra
        # Luego ya se crea el par de bloque/inodo
        if current_inode.i_block[i] == -1:
            next_free_block = get_next_free_block(fs, fs_start)
            if next_free_block == -1:
                print("FILESYSTEM->ERROR-> NO HAY BLOQUES DISPONIBLES")
                return 2

            set_block_usage(fs, fs_start, next_free_block, 1)

            base_block = DirectoryBlock(b_content=[
                Content(b_name=[b'-'] + [b'0']*11, b_inode=-1),
                Content(b_name=[b'-'] + [b'0']*11, b_inode=-1),
                Content(b_name=[b'-'] + [b'0']*11, b_inode=-1),
                Content(b_name=[b'-'] + [b'0']*11, b_inode=-1)
            ])

            fs.seek(super_block.s_block_start + next_free_block * struct.calcsize(directory_block_binary_format_string))
            write_struct_to_stream(fs, base_block)

            # Actualizar el puntero hacia este bloque
            current_inode.i_block[i] = next_free_block
            fs.seek(super_block.s_inode_start + current_inode_number * struct.calcsize(inode_binary_format_string))
            write_struct_to_stream(fs, current_inode)

        directory_block = DirectoryBlock()
        fs.seek(super_block.s_block_start + current_inode.i_block[i] * struct.calcsize(directory_block_binary_format_string))
        read_struct_from_stream(fs, directory_block, struct.calcsize(directory_block_binary_format_string))

        index = 0
        # Saltarse los primeros 2 punteros si es el primero, ya que hacen referencia al padre y a el mismo
        if i == 0:
            index = 2
            father_folder_name = directory_block.b_content[1].b_name.decode('utf-8').rstrip('\x00')

        for j in range(index, 4):
            if directory_block.b_content[j].b_inode != -1:
                continue

            next_free_inode = get_next_free_inode(fs, fs_start)
            next_free_block = get_next_free_block(fs, fs_start)
            # ##########################################################################################################
            user_perms = get_user_permissions_at_element(current_inode.i_perm, current_inode.i_uid, current_inode.i_gid)
            if not user_perms.write_perm:
                print("FILESYSTEM->ERROR-> EL USUARIO NO TIENE PERMISOS DE ESCRITURA EN EL PADRE DE <", directories[0], ">")
                return -10

            single_result = make_single_directory(disk_path, super_block, current_inode_number, directories,
                                                  next_free_inode, next_free_block, fs_start, directory_block, i, j,
                                                  current_inode.i_block[i], fs, father_folder_name)

            if single_result != 0:
                return single_result
            # ##########################################################################################################

            # Actualizar el tiempo de modificación del padre
            current_inode.i_modify_time = int(time.time())
            fs.seek(super_block.s_inode_start + current_inode_number * struct.calcsize(inode_binary_format_string))
            write_struct_to_stream(fs, current_inode)

            # Directorio mas alto creado, seguir con los demás
            new_dirs = directories[1:]
            return make_directories(disk_path, super_block, next_free_inode, new_dirs)

    print("FILESYSTEM->ERROR-> YA NO HAY ESPACIO PARA <", directories[0], ">. MÁXIMO DE HIJOS ES 62")
    return -1


# noinspection DuplicatedCode
def get_element_inode_number(fs, super_block, current_inode_number, directories, element_type):
    main_inode = Inode()
    fs.seek(super_block.s_inode_start + current_inode_number * struct.calcsize(inode_binary_format_string))
    read_struct_from_stream(fs, main_inode, struct.calcsize(inode_binary_format_string))

    # Archivo actuando como directorio
    if element_type == 0 and main_inode.i_type == b'1':
        print("FILESYSTEM->ERROR-> <", directories[0], "> es un archivo, no un directorio")
        return -2

    # Si ya terminamos de recorrer todos los elementos
    if not directories:  # TODO revisar si se necesita usar len(directories) == 0
        return current_inode_number

    for i in range(16):
        if main_inode.i_block[i] == -1:
            continue

        index = 0
        if i == 0:
            index = 2

        directory_block = DirectoryBlock()
        fs.seek(super_block.s_block_start + main_inode.i_block[i] * struct.calcsize(directory_block_binary_format_string))
        read_struct_from_stream(fs, directory_block, struct.calcsize(directory_block_binary_format_string))

        for j in range(index, 4):
            if directory_block.b_content[j].b_inode == -1:
                continue

            if directory_block.b_content[j].b_name.decode('utf-8').rstrip('\x00') == directories[0]:
                sus_node = Inode()
                fs.seek(super_block.s_inode_start + directory_block.b_content[j].b_inode * struct.calcsize(inode_binary_format_string))
                read_struct_from_stream(fs, sus_node, struct.calcsize(inode_binary_format_string))

                # Archivo actuando como directorio
                if element_type == 0 and sus_node.i_type == b'1':
                    print("FILESYSTEM->ERROR-> <", directories[0], "> es un archivo, no un directorio")
                    return -2

                if len(directories) == 1:
                    # Directorio actuando como archivo. Solo pasa en el ultimo elemento de la lista
                    if element_type == 1 and sus_node.i_type == b'0':
                        print("FILESYSTEM->ERROR-> <", directories[0], "> es un directorio, no un archivo")
                        return -2
                    return directory_block.b_content[j].b_inode

                new_dirs = directories[1:]
                return get_element_inode_number(fs, super_block, directory_block.b_content[j].b_inode, new_dirs, element_type)

    return -1


def decompose_file_path(filepath):
    result = []

    if filepath == "/":
        return result

    tokens = filepath.split("/")
    for token in tokens:
        if token != "":
            if len(token) > 12:
                print(f"FILESYSTEM->ADVERTENCIA-> <{token}> ES MAS LARGO QUE 12 CARACTERES, CORTANDO...")
                result.append(token[:12])
            else:
                result.append(token)

    return result


# noinspection DuplicatedCode
def get_next_free_inode(fs, fs_byte):
    sb = SuperBlock()
    fs.seek(fs_byte, os.SEEK_SET)
    read_struct_from_stream(fs, sb, struct.calcsize(super_block_binary_format_string))

    bm_inode = bytearray(sb.s_inodes_count)
    fs.seek(sb.s_bm_inode_start, os.SEEK_SET)
    data = fs.read(len(bm_inode))
    bm_inode[:len(data)] = data

    for i in range(sb.s_inodes_count):
        if bm_inode[i] == 0:
            return i

    return -1


# noinspection DuplicatedCode
def set_inode_usage(fs, fs_byte, n, state):
    if n < 0:
        print(f"FILESYSTEM->ERROR FATAL-> INTENTANDO LIBERAR INODO <{n}> NEGATIVO")
        return

    sb = SuperBlock()
    fs.seek(fs_byte, os.SEEK_SET)
    read_struct_from_stream(fs, sb, struct.calcsize(super_block_binary_format_string))

    bm_inode = bytearray(sb.s_inodes_count)
    fs.seek(sb.s_bm_inode_start, os.SEEK_SET)
    data = fs.read(len(bm_inode))
    bm_inode[:len(data)] = data

    bm_inode[n] = state
    fs.seek(sb.s_bm_inode_start, os.SEEK_SET)
    fs.write(bm_inode)
    fs.flush()

    # Marcando el siguiente disponible
    for i in range(sb.s_inodes_count):
        if bm_inode[i] == 0:
            sb.s_first_inode = i
            break

    # Actualizando la cantidad de inodos disponibles
    if state == 0:
        sb.s_free_inodes_count += 1
    else:
        sb.s_free_inodes_count -= 1

    fs.seek(fs_byte, os.SEEK_SET)
    write_struct_to_stream(fs, sb)


# noinspection DuplicatedCode
def get_next_free_block(fs, fs_byte):
    sb = SuperBlock()
    fs.seek(fs_byte, os.SEEK_SET)
    read_struct_from_stream(fs, sb, struct.calcsize(super_block_binary_format_string))

    bm_block = bytearray(sb.s_blocks_count)
    fs.seek(sb.s_bm_block_start, os.SEEK_SET)
    data = fs.read(len(bm_block))
    bm_block[:len(data)] = data

    for i in range(sb.s_blocks_count):
        if bm_block[i] == 0:
            return i

    return -1


# noinspection DuplicatedCode
def set_block_usage(fs, fs_byte, n, state):
    if n < 0:
        print(f"FILESYSTEM->ERROR FATAL-> INTENTANDO LIBERAR BLOQUE <{n}> NEGATIVO")
        return

    sb = SuperBlock()
    fs.seek(fs_byte, os.SEEK_SET)
    read_struct_from_stream(fs, sb, struct.calcsize(super_block_binary_format_string))

    bm_block = bytearray(sb.s_blocks_count)
    fs.seek(sb.s_bm_block_start, os.SEEK_SET)
    data = fs.read(len(bm_block))
    bm_block[:len(data)] = data

    bm_block[n] = state
    fs.seek(sb.s_bm_block_start, os.SEEK_SET)
    fs.write(bm_block)
    fs.flush()

    next_free_block = -1
    for i in range(sb.s_blocks_count):
        if bm_block[i] == 0:
            next_free_block = i
            break

    sb.s_first_block = next_free_block

    if state == 0:
        sb.s_free_blocks_count += 1
    else:
        sb.s_free_blocks_count -= 1

    fs.seek(fs_byte, os.SEEK_SET)
    write_struct_to_stream(fs, sb)


# noinspection DuplicatedCode
def initialize_file_system(fs, fs_byte):
    sb = SuperBlock()

    fs.seek(fs_byte, os.SEEK_SET)
    read_struct_from_stream(fs, sb, struct.calcsize(super_block_binary_format_string))

    sb.s_free_inodes_count -= 2
    sb.s_free_blocks_count -= 2
    sb.s_first_inode = 2
    sb.s_first_block = 2

    fs.seek(fs_byte, os.SEEK_SET)
    write_struct_to_stream(fs, sb)

    # Actualizar bm_inode para el inodo 0 para que apunte al bloque0 (que sera el archivo /users.txt)
    bm_inode = bytearray(sb.s_inodes_count)
    bm_inode[0] = 1
    bm_inode[1] = 1

    for i in range(2, sb.s_inodes_count):  # Rellenar de ceros, no es necesario?
        bm_inode[i] = 0

    fs.seek(sb.s_bm_inode_start, os.SEEK_SET)
    fs.write(bm_inode)
    fs.flush()

    # Actualizar bm_block para el bloque 0 para que tenga la info de users.txt
    bm_block = bytearray(sb.s_blocks_count)
    bm_block[0] = 1
    bm_block[1] = 1

    for i in range(2, sb.s_blocks_count):  # Rellenar de ceros, no es necesario?
        bm_block[i] = 0

    fs.seek(sb.s_bm_block_start, os.SEEK_SET)
    fs.write(bm_block)
    fs.flush()

    inode0 = Inode(i_uid=1,
                   i_gid=1,
                   i_size=struct.calcsize(inode_binary_format_string),
                   i_open_time=int(time.time()),
                   i_creation_time=int(time.time()),
                   i_modify_time=int(time.time()),
                   i_block=[0, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
                   i_type=b'0',
                   i_perm=644
                   )

    fs.seek(sb.s_inode_start + 0 * struct.calcsize(inode_binary_format_string), os.SEEK_SET)
    write_struct_to_stream(fs, inode0)

    block0 = DirectoryBlock()
    # block0.b_content[0] = Content([b'd', b's', b'k', b':', b'/', b'/', b'0', b'0', b'0', b'0', b'0', b'0'])
    # block0.b_content[1] = Content([b'd', b's', b'k', b':', b'/', b'/', b'0', b'0', b'0', b'0', b'0', b'0'])
    # block0.b_content[2] = Content([b'u', b's', b'e', b'r', b's', b'.', b't', b'x', b't', b'0', b'0', b'0'])
    # block0.b_content[3] = Content([b'-', b'0', b'0', b'0', b'0', b'0', b'0', b'0', b'0', b'0', b'0', b'0'])

    block0.b_content[0] = Content([element for element in b'/'], b_inode=0)
    block0.b_content[1] = Content([element for element in b'/'], b_inode=0)
    block0.b_content[2] = Content([element for element in b'users.txt'], b_inode=1)
    block0.b_content[3] = Content([element for element in b'-'], b_inode=-1)

    fs.seek(sb.s_block_start + 0 * struct.calcsize(directory_block_binary_format_string), os.SEEK_SET)
    write_struct_to_stream(fs, block0)

    inode1 = Inode(
        i_uid=1,
        i_gid=1,
        i_size=struct.calcsize(inode_binary_format_string),
        i_open_time=int(time.time()),
        i_creation_time=int(time.time()),
        i_modify_time=int(time.time()),
        i_block=[1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
        i_type=b'1',
        i_perm=644
    )

    fs.seek(sb.s_inode_start + 1 * struct.calcsize(inode_binary_format_string), os.SEEK_SET)
    write_struct_to_stream(fs, inode1)

    block1 = FileBlock()
    block1.b_content = bytearray(64)
    block1.b_content[:27] = b'1,G,root\n1,U,root,root,123\n'

    fs.seek(sb.s_block_start + 1 * struct.calcsize(file_block_binary_format_string), os.SEEK_SET)
    write_struct_to_stream(fs, block1)


# noinspection DuplicatedCode
def get_file_content(fs: io.FileIO | BinaryIO, super_block: SuperBlock, inode_number):
    inode_number = int(inode_number)
    file_inode = Inode()
    fs.seek(super_block.s_inode_start + inode_number * struct.calcsize(inode_binary_format_string), os.SEEK_SET)
    read_struct_from_stream(fs, file_inode, struct.calcsize(inode_binary_format_string))

    file_inode.i_open_time = int(time.time())
    fs.seek(super_block.s_inode_start + inode_number * struct.calcsize(inode_binary_format_string), os.SEEK_SET)
    write_struct_to_stream(fs, file_inode)

    content = ""
    for i in range(16):
        if file_inode.i_block[i] == -1:
            break  # Break en vez de continue porque el contenido de un archivo debe ser contiguo

        file_block = FileBlock()
        fs.seek(super_block.s_block_start + file_inode.i_block[i] * struct.calcsize(file_block_binary_format_string), os.SEEK_SET)
        read_struct_from_stream(fs, file_block, struct.calcsize(file_block_binary_format_string))

        for c in file_block.b_content:
            if c == 0:
                break
            content += chr(c)

    return content


# noinspection DuplicatedCode
def set_file_content(fs, super_block: SuperBlock, inode_number, content):
    fs_start = super_block.s_bm_inode_start - struct.calcsize(super_block_binary_format_string)

    required_size = len(content)

    # Primero, obtener el tamaño actual para ver si la nueva version utiliza menos bloques, para marcarlos como libres
    file_size = len(get_file_content(fs, super_block, inode_number))

    file_inode = Inode()
    fs.seek(super_block.s_inode_start + inode_number * struct.calcsize(inode_binary_format_string), os.SEEK_SET)
    read_struct_from_stream(fs, file_inode, struct.calcsize(inode_binary_format_string))
    file_inode.I_modify_time = int(time.time())
    fs.seek(super_block.s_inode_start + inode_number * struct.calcsize(inode_binary_format_string), os.SEEK_SET)
    write_struct_to_stream(fs, file_inode)

    for i in range(16):
        # Liberar bloques si ya no se necesitan
        if len(content) == 0:  # Si ya no hay contenido faltante
            if required_size < file_size or (required_size == 0 and file_size == 0):  # Y el archivo usaba mas espacio antes (o archivo vacío)
                if file_inode.i_block[i] != -1:  # Y este bloque esta marcado como usado
                    # Entonces, hay que liberarlo
                    set_block_usage(fs, fs_start, file_inode.i_block[i], 0)
                    # Llenar de 0's
                    file_block = FileBlock()
                    file_block.b_content = bytearray(64)
                    fs.seek(super_block.s_block_start + file_inode.i_block[i] * struct.calcsize(file_block_binary_format_string))
                    write_struct_to_stream(fs, file_block)
                    # El inodo ya no apunta a este bloque
                    file_inode.i_block[i] = -1
                    fs.seek(super_block.s_inode_start + inode_number * struct.calcsize(inode_binary_format_string))
                    write_struct_to_stream(fs, file_inode)

        # Crear un nuevo FileBlock si se necesita
        if file_inode.i_block[i] == -1 and len(content) > 0:
            # Bloque no existe, creando
            next_free_block = get_next_free_block(fs, fs_start)
            if next_free_block == -1:
                print("FILESYSTEM->ERROR-> NO HAY BLOQUES DISPONIBLES")
                return -2
            set_block_usage(fs, fs_start, next_free_block, 1)

            # Se llenara de 0's mas adelante

            # Actualizar el padre para que apunte a nosotros
            file_inode.i_block[i] = next_free_block
            fs.seek(super_block.s_inode_start + inode_number * struct.calcsize(inode_binary_format_string))
            write_struct_to_stream(fs, file_inode)

        file_block = FileBlock()
        fs.seek(super_block.s_block_start + file_inode.i_block[i] * struct.calcsize(file_block_binary_format_string), os.SEEK_SET)
        read_struct_from_stream(fs, file_block, struct.calcsize(file_block_binary_format_string))

        for j in range(len(file_block.b_content)):
            if len(content) == 0:
                file_block.b_content[j] = 0
            else:
                file_block.b_content[j] = ord(content[0])
                content = content[1:]

        fs.seek(super_block.s_block_start + file_inode.i_block[i] * struct.calcsize(file_block_binary_format_string))
        write_struct_to_stream(fs, file_block)

    # Caso de de que se haya escrito el contenido completo
    if len(content) == 0:
        return 0

    # Caso de que se haya excedido el limite
    print(f"FILESYSTEM->ERROR-> MÁXIMO TAMAÑO DE ARCHIVO SOBREPASADO. FALTA ESPACIO PARA {len(content)} CARACTERES")
    return len(content)


def get_user_permissions_at_element(element_permissions, owner_uid, owner_gid):
    user_uid = LoggedUser.uid
    user_gid = LoggedUser.gid
    perms = Permissions()

    # Usuario Root
    if user_uid == 1:
        return Permissions(write_perm=True, read_perm=True, execute_perm=True)

    # TODO revisar que funcione bien, cambiado drásticamente
    def individual_perms(ind):
        # Read (4)
        read_permission = ind >= 4
        # Write (2)
        write_permission = (ind % 4) >= 2
        # Execute (1)
        execute_permission = (ind % 2) == 1
        return read_permission, write_permission, execute_permission

    # Other
    number = element_permissions % 10
    element_permissions = element_permissions // 10
    (other_r, other_w, other_e) = individual_perms(number)
    perms.read_perm |= other_r
    perms.write_perm |= other_w
    perms.execute_erm |= other_e

    # Group
    number = element_permissions % 10
    element_permissions = element_permissions // 10
    if user_gid == owner_gid:
        (other_r, other_w, other_e) = individual_perms(number)
        perms.read_perm |= other_r
        perms.write_perm |= other_w
        perms.execute_erm |= other_e

    # Owner
    number = element_permissions
    if user_uid == owner_uid:
        (other_r, other_w, other_e) = individual_perms(number)
        perms.read_perm |= other_r
        perms.write_perm |= other_w
        perms.execute_erm |= other_e

    return perms


def list_directory(fs, super_block: SuperBlock, current_inode_number, recursive, prefix):
    main_inode = Inode()
    fs.seek(super_block.s_inode_start + current_inode_number * struct.calcsize(inode_binary_format_string))
    read_struct_from_stream(fs, main_inode, struct.calcsize(inode_binary_format_string))

    files = []

    for index_k in range(16):
        if main_inode.i_block[index_k] == -1:
            continue
        index = 0
        if index_k == 0:
            index = 2
        directory_block = DirectoryBlock()
        fs.seek(super_block.s_block_start + main_inode.i_block[index_k] * struct.calcsize(directory_block_binary_format_string), os.SEEK_SET)
        read_struct_from_stream(fs, directory_block, struct.calcsize(directory_block_binary_format_string))

        for index_l in range(index, 4):
            if directory_block.b_content[index_l].b_inode == -1:
                continue
            the_node = Inode()
            fs.seek(super_block.s_inode_start + directory_block.b_content[index_l].b_inode * struct.calcsize(inode_binary_format_string), os.SEEK_SET)
            read_struct_from_stream(fs, the_node, struct.calcsize(inode_binary_format_string))
            if the_node.i_type == '1':
                files.append(DirectoryElement(
                    is_directory=False,
                    name=prefix + directory_block.b_content[index_l].b_name.rstrip(b'\x00').decode('utf-8'),
                    inode_number=directory_block.b_content[index_l].b_inode
                ))
            else:
                files.append(DirectoryElement(
                    is_directory=True,
                    name=prefix + directory_block.b_content[index_l].b_name.rstrip(b'\x00').decode('utf-8'),
                    inode_number=directory_block.b_content[index_l].b_inode
                ))
                if recursive:
                    nested = list_directory(fs, super_block, directory_block.b_content[index_l].b_inode, recursive, prefix + directory_block.b_content[index_l].b_name.rstrip(b'\x00').decode('utf-8') + "/")
                    files.extend(nested)

    return files


# noinspection DuplicatedCode
def get_user_name_by_uid(fs, super_block, uid):
    pattern = f"{uid},U,[^,]*,([^,]*),[^\n]*"
    regex = re.compile(pattern, re.MULTILINE)

    file_node_number = get_element_inode_number(fs, super_block, 0, ["users.txt"], 1)
    users_file = get_file_content(fs, super_block, file_node_number)

    match = regex.search(users_file)
    if match is None:
        return ""
    return match.group(1)


# noinspection DuplicatedCode
def get_group_name_by_gid(fs, super_block, gid):
    pattern = f"{gid},G,([^\n]*)"
    regex = re.compile(pattern, re.MULTILINE)

    file_node = get_element_inode_number(fs, super_block, 0, ["users.txt"], 1)
    users_file = get_file_content(fs, super_block, file_node)

    match = regex.search(users_file)
    if match is None:
        return ""
    return match.group(1)


def get_perms_as_rwx_string(perms, is_dir):
    final = "d" if is_dir else "-"
    for _ in range(3):
        next_digit = perms % 10
        perms //= 10
        read_permission = "r" if next_digit >= 4 else "-"
        write_permission = "w" if (next_digit % 4) >= 2 else "-"
        execute_permission = "x" if (next_digit % 2) == 1 else "-"
        final += f"{read_permission}{write_permission}{execute_permission}"
    return final
