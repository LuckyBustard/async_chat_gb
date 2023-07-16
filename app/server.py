import threading
import time
import logging
from socket import socket, AF_INET, SOCK_STREAM
from select import select
from common import vars
from common.abstract_messenger import AbstractMessenger
from common.meta_classes import ServerMaker
from deorators.call_logger import CallLogger
from common.server_database import ServerStorage


class Server(AbstractMessenger, threading.Thread, metaclass=ServerMaker):
    def __init__(self, database):
        super().__init__()
        self.transport: socket = None
        self.logger = logging.getLogger('app.server')
        self.get_config_data()
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
    def process_client_message(self, client_sock: socket):
        """
        Получение сообщения от клиента и постановка его в очередь сообщений

        :param users:
        :param client_sock:
        :param wait_messages:
        :return:
        """
        message = self.get_message(client_sock)

        self.logger.debug(f'receive new message {message}')
        if vars.ACTION in message and vars.TIME in message and vars.USER in message:
            # Страшно переходить на версию 3.10 но очень хочется матч кейс
            if message[vars.ACTION] == vars.PRESENCE:
                if message[vars.USER][vars.ACCOUNT_NAME] not in self.users_list.keys():
                    self.users_list[message[vars.USER][vars.ACCOUNT_NAME]] = client_sock
                    client_ip, client_port = client_sock.getpeername()
                    self.database.user_login(message[vars.USER][vars.ACCOUNT_NAME], client_ip, client_port)
                    self.send_message(self.create_response())
                else:
                    self.send_message(self.create_response('Имя пользователя уже занято.'))
                    client_sock.close()

            elif message[vars.ACTION] == vars.MESSAGE and vars.DESTINATION in message:
                self.logger.debug('message ok')
                self.waiting_messages.append(
                    (message[vars.USER], message[vars.MESSAGE_TEXT], message[vars.DESTINATION]))
                self.send_message(self.create_response())

            elif message[vars.ACTION] == vars.EXIT:
                client_sock.close()
                self.database.user_logout(message[vars.ACCOUNT_NAME])
                del self.users_list[message[vars.USER][vars.ACCOUNT_NAME]]

            return

        self.logger.error('message fail')
        return self.create_response('Bad request')

    @CallLogger()
    def message_sender(self, user_name: str, message: dict):
        try:
            self.send_message(self.users_list[user_name], message)
        except Exception as e:
            self.logger.info(f'Client {self.users_list[user_name].getpeername()} disconnected. 2 {e}')
            self.connected_clients.remove(self.users_list[user_name])
            del self.users_list[user_name]

    @CallLogger()
    def message_sender_broadcast(self, send_queue: list, message: dict):
        for waiting_client in send_queue:
            try:
                self.send_message(waiting_client, message)
            except Exception as e:
                self.logger.info(f'Client {waiting_client.getpeername()} disconnected. 1 {e}')
                self.connected_clients.remove(waiting_client)

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
                        self.logger.info(f'Client {waiting_messanger.getpeername()} disconnected. {e}')
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


def print_help():
    print('Поддерживаемые комманды:')
    print('users - список известных пользователей')
    print('connected - список подключенных пользователей')
    print('loghist - история входов пользователя')
    print('exit - завершение работы сервера.')
    print('help - вывод справки по поддерживаемым командам')


def main():
    database = ServerStorage()
    server = Server(database)
    server.daemon = True

    server.start()

    print_help()
    time.sleep(5)
    server.logger.debug(sorted(database.users_list()))

    while True:
        while True:
            command = input('Введите комманду: ')
            if command == 'help':
                print_help()
            elif command == 'exit':
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
