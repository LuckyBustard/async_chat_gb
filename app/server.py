import configparser
import os
import sys
import threading
import time
import logging
from socket import socket, AF_INET, SOCK_STREAM
from select import select

from PyQt6.QtWidgets import QApplication, QMessageBox

from common import vars
from gui.server_gui import MainWindow, gui_create_model, ConfigWindow, HistoryWindow, create_stat_model
from messagers.server_messenger import ServerMessenger
from meta_classes.server_maker import ServerMaker
from deorators.call_logger import CallLogger
from database.server_database import ServerStorage


config = configparser.ConfigParser()


class Server(ServerMessenger, threading.Thread, metaclass=ServerMaker):
    def __init__(self, database):
        super().__init__()
        self.transport: socket = None
        self.logger = logging.getLogger('app.server')
        self.get_config_data(config['SETTINGS']['Listen_Address'], config['SETTINGS']['Default_port'])
        self.logger.info(f'server starting, listen ip {self.listen_host}, server port {self.listen_host}')
        self.connected_clients = []
        self.waiting_messages = []
        self.users_list = dict()
        self.database = database

    def init_socket(self):
        self.transport = socket(AF_INET, SOCK_STREAM)
        self.transport.bind((self.listen_host, self.listen_port))
        self.transport.listen(vars.MAX_CONNECTIONS)
        self.transport.settimeout(0.5)

    @CallLogger()
    def close(self):
        self.transport.close()

    @CallLogger()
    def run(self):
        self.init_socket()

        while True:
            try:
                client, client_address = self.transport.accept()
            except OSError:
                pass
            else:
                self.connected_clients.append(client)
                self.logger.info(f'accept connection from {client_address}')

            recv_queue = []
            send_queue = []
            err_lst = []
            try:
                if self.connected_clients:
                    recv_queue, send_queue, err_lst = select(self.connected_clients, self.connected_clients, [], 0)
            except OSError:
                pass

            if recv_queue:
                for waiting_messanger in recv_queue:
                    try:
                        self.process_client_message(waiting_messanger)
                    except Exception as e:
                        self.logger.info(f'Client {waiting_messanger.getpeername()} disconnected 3. {e}')
                        self.connected_clients.remove(waiting_messanger)

            if self.waiting_messages and send_queue:
                for wait_message in self.waiting_messages:
                    user_name = wait_message[2]
                    message = {
                        vars.ACTION: vars.MESSAGE,
                        vars.USER: wait_message[0],
                        vars.TIME: time.time(),
                        vars.MESSAGE_TEXT: wait_message[1]
                    }
                    self.waiting_messages.remove(wait_message)

                    if wait_message[2] == vars.DESTINATION_ALL:
                        self.message_sender_broadcast(send_queue, message)
                    else:
                        self.message_sender(user_name, message)

    def print_help(self):
        print('Поддерживаемые комманды:')
        print('users - список известных пользователей')
        print('connected - список подключенных пользователей')
        print('loghist - история входов пользователя')
        print('exit - завершение работы сервера.')
        print('help - вывод справки по поддерживаемым командам')


def main():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")

    if 'SETTINGS' not in config:
        config['SETTINGS'] = {}
        config['SETTINGS']['Default_port'] = ''
        config['SETTINGS']['Listen_Address'] = ''
        config['SETTINGS']['Database_path'] = ''
        config['SETTINGS']['Database_file'] = ''

    database = ServerStorage()
    server = Server(database)
    server.daemon = True

    server.start()

    server.print_help()

    server_app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.statusBar().showMessage('Server Working')
    main_window.active_clients_table.setModel(gui_create_model(database))
    main_window.active_clients_table.resizeColumnsToContents()
    main_window.active_clients_table.resizeRowsToContents()

    def list_update():
        main_window.active_clients_table.setModel(
            gui_create_model(database))
        main_window.active_clients_table.resizeColumnsToContents()
        main_window.active_clients_table.resizeRowsToContents()

    # Функция создающяя окно со статистикой клиентов
    def show_statistics():
        global stat_window
        stat_window = HistoryWindow()
        stat_window.history_table.setModel(create_stat_model(database))
        stat_window.history_table.resizeColumnsToContents()
        stat_window.history_table.resizeRowsToContents()
        stat_window.show()

    # Функция создающяя окно с настройками сервера.
    def server_config():
        global config_window
        # Создаём окно и заносим в него текущие параметры
        config_window = ConfigWindow()
        config_window.db_path.insert(config['SETTINGS']['Database_path'])
        config_window.db_file.insert(config['SETTINGS']['Database_file'])
        config_window.port.insert(config['SETTINGS']['Default_port'])
        config_window.ip.insert(config['SETTINGS']['Listen_Address'])
        config_window.save_btn.clicked.connect(save_server_config)

    # Функция сохранения настроек
    def save_server_config():
        global config_window
        message = QMessageBox()
        config['SETTINGS']['Database_path'] = config_window.db_path.text()
        config['SETTINGS']['Database_file'] = config_window.db_file.text()
        try:
            port = int(config_window.port.text())
        except ValueError:
            message.warning(config_window, 'Ошибка', 'Порт должен быть числом')
        else:
            config['SETTINGS']['Listen_Address'] = config_window.ip.text()
            if 1023 < port < 65536:
                config['SETTINGS']['Default_port'] = str(port)
                print(port)
                with open('server.ini', 'w') as conf:
                    config.write(conf)
                    message.information(
                        config_window, 'OK', 'Настройки успешно сохранены!')
            else:
                message.warning(
                    config_window,
                    'Ошибка',
                    'Порт должен быть от 1024 до 65536')

    main_window.refresh_button.triggered.connect(list_update)
    main_window.show_history_button.triggered.connect(show_statistics)
    main_window.config_btn.triggered.connect(server_config)

    server_app.exec()

    while True:
        command = input('Введите комманду: ')
        if command == 'help':
            server.print_help()
        elif command == 'exit':
            server.close()
            break
        elif command == 'users':
            for user in sorted(database.users_list()):
                print(f'Пользователь {user[0]}, последний вход: {user[1]}')
        elif command == 'connected':
            for user in sorted(database.active_users_list()):
                print(
                    f'Пользователь {user[0]}, подключен: {user[1]}:{user[2]}, время установки соединения: {user[3]}')
        elif command == 'loghist':
            name = input(
                'Введите имя пользователя для просмотра истории. Для вывода всей истории, просто нажмите Enter: ')
            for user in sorted(database.login_history(name)):
                print(f'Пользователь: {user[0]} время входа: {user[1]}. Вход с: {user[2]}:{user[3]}')
        else:
            print('Команда не распознана.')


if __name__ == '__main__':
    main()
