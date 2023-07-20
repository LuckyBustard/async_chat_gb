import threading
import time
import sys
import logging
from meta_classes.client_maker import ClientMaker
from socket import socket, AF_INET, SOCK_STREAM
from messagers.client_messenger import ClientMessenger
from database.client_database import ClientStorage
from deorators.call_logger import CallLogger


class Client(ClientMessenger, metaclass=ClientMaker):
    def __init__(self):
        super().__init__()
        self.sock = None
        self.logger = logging.getLogger('app.client')
        self.get_config_data()
        self.logger.info('connected to server')
        self.database = ClientStorage(self.account_name)

    def connect(self):
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.sock.settimeout(1)
        self.sock.connect((self.listen_host, self.listen_port))

    def runner(self):
        self.connect()

        receiver = threading.Thread(target=self.receive_message)
        receiver.daemon = True
        receiver.start()

        sender = threading.Thread(target=self.create_meesage)
        sender.daemon = True
        sender.start()

        while True:
            try:
                time.sleep(1)
                if receiver.is_alive() and sender.is_alive():
                    continue
                break

            except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
                self.logger.error(f'Соединение с сервером {self.listen_host} было потеряно.')
                sys.exit(1)


if __name__ == '__main__':
    client = Client()
    client.runner()
