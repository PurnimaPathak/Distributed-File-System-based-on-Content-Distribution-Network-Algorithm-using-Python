import os
import signal
import socket

from business_logic import get_data, get_list, put_data
from utils import shutdown, parse_filename, parse_request, user_valid, parse_cred


class Server:
    """

    """
    def __init__(self, config, root_folder, port):
        """

        :param config:
        """
        signal.signal(signal.SIGINT, shutdown)  # Shutdown on Ctrl+C
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a TCP socket
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Re-use the socket
        self.serverSocket.bind((config['HOSTNAME'], port))  # bind the socket to a public host, and a port
        self.serverSocket.listen(10)  # become a server socket
        self.config = config
        self.__clients = {}
        self.root_dir = root_folder

        if not os.path.exists(self.root_dir):
            os.makedirs(self.root_dir)

    def listen_from_client(self):
        """

        :return:
        """
        print("Listening....")
        while True:
            (client_socket, client_address) = self.serverSocket.accept()  # Establish the connection
            # d = threading.Thread(name=self._getClientName(client_address),
            #                      target=self.listen(client_socket, client_address),
            #                      args=(client_socket, client_address))
            # d.setDaemon(True)
            # d.start()
            self.listen(client_socket, client_address)
        shutdown(self.serverSocket, 0, 0)

    def _getClientName(self, client_address):
        return "Client"

    def listen(self, client_socket, client_address):
        request_client = client_socket.recv(int(self.config['MAX_REQUEST_LEN']))
        print("Recieved request from client:")
        print(request_client)
        request_method = parse_request(request_client)
        uname, pswd = parse_cred(request_client)
        if not user_valid(uname, pswd, self.config):
            client_socket.send("Unauthorised")
            client_socket.close()
            return
        udir = self.root_dir + "/" + uname
        if request_method == "GET":
            get_data(client_socket, udir + "/" + parse_filename(request_client))
        if request_method == "PUT":
            client_socket.send("Authorised")
            return put_data(udir, client_socket, request_client)
        if request_method == "LIST":
            get_list(udir, client_socket)
            client_socket.close()


