import os

from utils import parse_filename


def get_data(client_socket, filename):
    """
    request_client = GET filename.txt
    :param request_client:
    :return:
    """
    try:
        with open(filename, 'rb') as file:
            for data in file.readlines():
                client_socket.send(data)
            client_socket.close()
    except Exception as e:
        client_socket.send("Wrong User".encode())


def get_list(directory, client_socket):
    """

    :param directory:
    :param client_socket:
    :return:
    """
    try:
        client_socket.send(" ".join(os.listdir(directory)).encode())
        client_socket.close()
    except Exception as e:
        client_socket.send("Wrong User".encode())


def put_data(user_dir, client_socket, request_client):
    if not os.path.exists(user_dir):
        print("User dir: {}".format(user_dir))
        os.makedirs(user_dir)
    with open(user_dir + "/" + parse_filename(request_client), 'wb') as file:
        data = client_socket.recv(65535)
        file.write(data)
        file.close()
        client_socket.close()
        return