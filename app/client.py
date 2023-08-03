import threading
import time
import sys
import logging

from PyQt6.QtWidgets import QApplication

from meta_classes.client_maker import ClientMaker
from socket import socket, AF_INET, SOCK_STREAM
from messagers.client_messenger import ClientMessenger
from database.client_database import ClientStorage
from deсorators.call_logger import CallLogger
from gui.main_window import ClientMainWindow
from gui.start_dialog import UserNameDialog


class Client(ClientMessenger, metaclass=ClientMaker):
    """fdsfds Основной 111 класс для запуска клиентского приложения. Подключение, отправка сообщений GUI интерфейс"""

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
        """Основной метод для подключения и работы с сервером"""
        self.connect()

        client_app = QApplication(sys.argv)

        start_dialog = UserNameDialog()
        if not self.account_name or not self.password:
            client_app.exec()
            # Если пользователь ввёл имя и нажал ОК, то сохраняем ведённое и
            # удаляем объект, инааче выходим
            if start_dialog.ok_pressed:
                client_name = start_dialog.client_name.text()
                client_passwd = start_dialog.client_passwd.text()
            else:
                exit(0)

        receiver = threading.Thread(target=self.receive_message)
        receiver.daemon = True
        receiver.start()

        sender = threading.Thread(target=self.create_meesage)
        sender.daemon = True
        sender.start()

        del start_dialog
        main_window = ClientMainWindow(self)
        #main_window.make_connection(self)
        main_window.setWindowTitle(f'Чат Программа alpha release - {self.account_name}')
        client_app.exec()

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
