import sys

from constants import FILE_URL
from server import Server
from utils import read_config


def run_server(root_folder, port):
    config = read_config(FILE_URL)
    server_obj = Server(config, root_folder, port)
    server_obj.listen_from_client()
    pass


if __name__ == "__main__":

    if len(sys.argv) < 3:
        print("Folder name and Port number required, Example 'python dfs /DFS1 10001'")
        exit()

    run_server(sys.argv[1], int(sys.argv[2]))
    # run_server("./DFS4", 10004)
