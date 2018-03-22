import sys


def read_config(url="./dfs.conf"):
    conf_file = open(url)
    conf = {}
    for line in conf_file.readlines():
        if "HOSTNAME" in line:
            conf['HOSTNAME'] = line.split()[1].strip()
        if 'MAX_REQUEST_LEN' in line.split():
            conf['MAX_REQUEST_LEN'] = int(line.split()[1].strip())
        if "Password" in line:
            if "User" not in conf.keys():
                conf["User"] = {line.split()[1].strip(): line.split()[3].strip()}
            else:
                conf["User"][line.split()[1].strip()] = line.split()[3].strip()
    return conf


def shutdown(serverSocket, signum, frame):
    """ Handle the exiting server. Clean all traces """
    serverSocket.close()
    sys.exit(0)


def parse_filename(request_client):
    # TODO split the filename from part
    filename = request_client.split()[1].decode()
    return remove_null_byte(filename)


def encrypt_data(request_client):
    return request_client


def parse_request(request_client):
    method = request_client.split()[0].strip()
    if method.decode() in ["GET", "PUT", "LIST"]:
        return method.decode()
    else:
        raise


def remove_null_byte(string_with_null_byte):
    """

    :param string_with_null_byte:
    :return:
    """
    return_str = string_with_null_byte.encode()
    return b"".join(return_str.split(b'\x00')).decode()


def parse_cred(request_client):
    """

    :param request_client:
    :return:
    """
    decoded_request = remove_null_byte(request_client.decode())
    user = decoded_request.split("Username:")[1].split()[0].strip()

    password = decoded_request.split("Password:")[1].split()[0].strip()
    return user, password


def user_valid(user, password, conf):
    """

    :param user:
    :param password:
    :param conf:
    :return:
    """
    if user not in conf["User"].keys():
        return False
    if password != conf["User"][user]:
        return False
    return True

