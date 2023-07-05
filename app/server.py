import time
import logging
from select import select
from socket import socket, AF_INET, SOCK_STREAM
from common import vars
from common.abstract_messenger import AbstractMessenger
from deorators.call_logger import CallLogger
from common.meta_classes import ServerMaker
import loggers.server_logs


class Server(AbstractMessenger, metaclass=ServerMaker):
    transport: socket
    connected_clients = []
    waiting_messages = []
    users_list = dict()

    def __init__(self):
        self.logger = logging.getLogger('app.server')
        self.get_config_data()
        self.logger.info(f'server starting, listen ip {self.listen_host}, server port {self.listen_host}')

    @CallLogger()
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
    def runner(self):
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


if __name__ == '__main__':
    server = Server()
    server.runner()
