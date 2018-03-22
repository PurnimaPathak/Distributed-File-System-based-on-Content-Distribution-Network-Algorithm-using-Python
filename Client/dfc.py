import hashlib
import os
import socket

import sys

import time

UPLOAD_PAIR_MATRIX = [
    [[0, 1], [1, 2], [2, 3], [3, 0]],
    [[3, 0], [0, 1], [1, 2], [2, 3]],
    [[2, 3], [3, 0], [0, 1], [1, 2]],
    [[1, 2], [2, 3], [3, 0], [0, 1]]
]


def read_config(url="./dfc.conf"):
    conf_file = open(url)
    conf = {'SERVER': []}
    for line in conf_file.readlines():
        if "Server" in line.split():
            address = line.split()[2].strip().split(":")
            conf['SERVER'].append((address[0], int(address[1])))
        if 'MAX_REQUEST_LEN' in line.split():
            conf['MAX_REQUEST_LEN'] = line.split()[1].strip()
        if 'Username' in line:
            conf['Username'] = line.split(":")[1].strip()
        if 'Password' in line:
            conf['Password'] = line.split(":")[1].strip()
        if 'MAX_REQUEST_LEN' in line:
            conf['MAX_REQUEST_LEN'] = int(line.split()[1].strip())
    return conf


def PUT(conf, filename):
    """
    (1,2)(2,3)(3,4)(4,1)
    (4,1)(1,2)(2,3)(3,4)

    x ??  MD5hash(filename) % 4 >> 0,1,2,3
    :param conf:
    :param filename:
    :return:
    """
    with open(filename, 'rb') as file:
        lines = file.readlines()
    num_lines = len(lines)
    limit = int(num_lines / 4)
    parts_list = [
        {"start": None, "end": limit},
        {"start": limit, "end": limit * 2},
        {"start": limit * 2, "end": limit * 3},
        {"start": limit * 3, "end": None},
    ]

    x = ord(hashlib.md5(filename.encode('utf-8')).hexdigest()[-1])%4

    print("Hash value x is {} and upload pair is {}".format(x, UPLOAD_PAIR_MATRIX[x]))

    DFS = 0
    for upload_pair in UPLOAD_PAIR_MATRIX[x]:

        start = parts_list[upload_pair[0]]['start']
        end = parts_list[upload_pair[0]]['end']
        print("File part{}: start {}, end {}".format(upload_pair[0], start, end))

        user_cred = {
            "USER": conf['Username'],
            "PASS": conf['Password']
        }

        send_part_file(
            lines[start:end],
            conf['SERVER'][DFS],
            ".{}.{}".format(filename, upload_pair[0]),
            user_cred
        )

        start = parts_list[upload_pair[1]]['start']
        end = parts_list[upload_pair[1]]['end']
        print("File part{}: start {}, end {}".format(upload_pair[1], start, end))

        send_part_file(
            lines[start:end],
            conf['SERVER'][DFS],
            ".{}.{}".format(filename, upload_pair[1]),
            user_cred
        )
        DFS += 1

    print("PUT completed")


def send_part_file(lines, host_address, filename, cred):
    try:
        s_socket = socket.socket()
        s_socket.connect(host_address)
        s_socket.send("PUT {} Username: {} Password: {}".format(filename, cred["USER"], cred["PASS"]).encode())
        data = s_socket.recv(1024)
        if "Unauthorised" == data.decode():
            raise ValueError("Username password didn't match")
        print("Sending data to {}:{}".format(host_address[0], host_address[1]))
        time.sleep(10)
        data = b''.join(lines)
        s_socket.sendall(data)
        s_socket.close()
    except ValueError as err:
        raise ValueError("Username password didn't match")
    except Exception as e:
        print("Error: {}".format(e))
    finally:
        s_socket.close()


def get_part(server_addr, filename, cred):
    part = None
    try:
        print("Getting part file from {}:{}".format(server_addr[0], server_addr[1]))
        server_sock = socket.socket()
        server_sock.connect(server_addr)
        server_sock.send("GET {} Username: {} Password: {}".format(filename, cred["USER"], cred["PASS"]).encode())
        server_sock.settimeout(1.0)
        data = server_sock.recv(1024)
        if "Unauthorised" in data.decode():
            raise ValueError("Username password didn't match")
        if "Wrong User" == data.decode():
            raise FileNotFoundError("Wrong user of file name")
        part = data
        while data:
            data = server_sock.recv(1024)  # (self.config['MAX_REQUEST_LEN'])
            part += data
        server_sock.close()
    except FileNotFoundError as e:
        raise FileNotFoundError("Wrong user of file name")
    except ValueError as err:
        raise ValueError("Username password didn't match")
    except Exception as e:
        print("Data not recieved")
        print("Error: {}".format(e))
    return part


def get_part_file(server1, server2, filename, cred):
    """
    
    :param server_sock:
    :param server1:
    :param server2:
    :param filename:
    :return:
    """
    part = get_part(server1, filename, cred)
    if not part:
        part = get_part(server2, filename, cred)
    return part


def get_server_list(conf, file_name, part):
    x = ord(hashlib.md5(file_name.encode('utf-8')).hexdigest()[-1]) % 4
    serverlist = []
    DFS = 0
    for upload_pair in UPLOAD_PAIR_MATRIX[x]:
        if part in upload_pair:
            serverlist.append(conf['SERVER'][DFS])
        DFS += 1
    return serverlist


def GET(conf, file_name):
    """

    :param conf:
    :param server_sock:
    :param file_name:
    :return:
    """
    parts = []
    user_cred = {
        "USER": conf['Username'],
        "PASS": conf['Password']
    }

    file_data = b''
    save_file_name = file_name
    for i in range(4):
        s_list = get_server_list(conf, file_name, i)
        parts.append(get_part_file(s_list[0],
                                   s_list[1],
                                   ".{}.{}".format(file_name, str(i)),
                                   user_cred
                                   ))
        save_file_name, file_data = concat_part(save_file_name, parts[i], file_data)

    if None in parts:
        print("File is incomplete.")
        return
    print("GET completed, saving data to file")
    print("\nWriting to {}".format(save_file_name))
    file = open(save_file_name, 'wb')
    file.write(file_data)
    file.close()
    print("File saved")


def concat_part(file_name, part1, file_data):
    """

    :param file_name:
    :param part1:
    :return:
    """
    if part1:
        file_data += part1
    else:
        file_name += ' [incomplete]' if 'incomplete' not in file_name else ''
    return file_name, file_data


def get_list(server_address, cred):
    try:
        server_sock = socket.socket()
        server_sock.connect(server_address)
        server_sock.send("LIST Username: {} Password: {}".format(cred["USER"], cred["PASS"]).encode())
        data = server_sock.recv(1024)
        if "Unauthorised" in data.decode():
            raise ValueError("Invalid Credentials or filename")
        if "Wrong User" == data.decode():
            raise FileNotFoundError("Username password didn't match")
        server_sock.close()
        return data.decode().split() 
    except FileNotFoundError as e:
        raise FileNotFoundError("Wrong user of file name")
    except ValueError as err:
        raise ValueError("Username password didn't match")
    except Exception as e:
        print("Error: {}".format(e))
        return []


def create_final_list(list_data):
    """
    list_data = {serv1: [1_1, 1_2, 2, 3, 4]
                 #serv2: [1_2, 1_3]
                 #serv3: [1_3, 1_4]
                 serv4: [1_4, 1_1]
                }
    :param list_data:
    :return:
    """
    file_set = set(list_data)
    file_name = file_set.pop()[1:-2]
    files = {}

    while len(file_set) > 0:
        if file_name not in files.keys():
            files[file_name] = 2
        else:
            files[file_name] += 1
        file_name = file_set.pop()[1:-2]
    final_list = []
    for key, value in files.items():
        if value < 4:
            final_list.append("{} [incomplete]".format(key))
        else:
            final_list.append(key)
    return final_list


def LIST(conf):
    """
    conf = {"SERVER": [(ip, port), (ip2, port2), ...}

    :param conf:
    :param server_sock:
    :return:
    """
    list_data = []
    for server_add in conf["SERVER"]:
        list_data.extend(get_list(server_add, {"USER": conf['Username'], "PASS": conf['Password']}))
    part_files = set(list_data)
    final_list = create_final_list(part_files)
    print("\n".join(final_list))


def main():
    """

    :return:
    """
    conf = read_config()
    while True:
        try:
            command = input()
            method = command.split()[0] # GET 1.txt, PUT 1.txt, LIST
            if method not in ["GET", "PUT", "LIST"]:
                print("Wrong method. Please try again with method name as GET, PUT or LIST")
            if method == "PUT":
                if os.path.exists(command.split()[1]):  # TODO if folder name provided without filename
                    PUT(conf, command.split()[1])
            # TODO: implement LIST
            if method == "GET":
                GET(conf, command.split()[1])
            if method == "LIST":
                LIST(conf)
        except ValueError as e:
            print(e)
        except Exception as e:
            print(e)
            print("Please try again with method name as GET, PUT or LIST")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)
