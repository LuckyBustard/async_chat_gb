"""Месседжер модуль для работы сервера"""
import binascii
import hmac
import os
from socket import socket
from common import variables
from deсorators.login_required import login_required
from messagers.abstract_messenger import AbstractMessenger
from deсorators.call_logger import CallLogger

class ServerMessenger(AbstractMessenger):
    """Класс месседжер сервера, обработка сообщений от клиентов"""

    def authorise_user(self, client_socket, message):
        """Авторизация пользователя"""
        message_auth = self.create_response(511)
        random_str = binascii.hexlify(os.urandom(64))
        message_auth[variables.DATA] = random_str.decode('ascii')
        hash_data = hmac.new(
            self.database.get_hash(message[variables.USER][variables.ACCOUNT_NAME]),
            random_str,
            'MD5'
        )
        digest = hash_data.digest()

        self.send_message(client_socket, message_auth)
        answer = self.get_message(client_socket)
        client_digest = binascii.a2b_base64(answer[variables.DATA])

        if variables.RESPONSE in answer and answer[variables.RESPONSE] == 511 and hmac.compare_digest(
                digest, client_digest):
            client_ip, client_port = client_socket.getpeername()
            self.database.user_login(
            message[variables.USER][variables.ACCOUNT_NAME],
            client_ip,
            client_port,
            message[variables.USER][variables.PUBLIC_KEY])

            self.users_list[message[variables.USER][variables.ACCOUNT_NAME]] = client_socket
            self.send_message(client_socket, self.create_response())
        else:
            try:
                self.send_message(client_socket, self.create_response(400, 'Неверный пароль'))
            except OSError:
                pass
            self.clients.remove(client_socket)
            client_socket.close()

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
        if variables.ACTION in message and variables.TIME in message and variables.USER in message:
            # Страшно переходить на версию 3.10 но очень хочется матч кейс
            if message[variables.ACTION] == variables.PRESENCE:
                if message[variables.USER][variables.ACCOUNT_NAME] not in self.users_list.keys() \
                        and self.database.check_user(message[variables.USER][variables.ACCOUNT_NAME]):
                    self.authorise_user(client_sock, message)
                else:
                    self.send_message(
                        client_sock,
                        self.create_response('Имя пользователя уже занято.')
                    )
                    client_sock.close()

            elif message[variables.ACTION] == variables.MESSAGE and variables.DESTINATION in message:
                self.waiting_messages.append(
                    (message[variables.USER], message[variables.MESSAGE_TEXT], message[variables.DESTINATION]))
                self.database.process_message(
                    message[variables.USER],
                    message[variables.DESTINATION]
                )
                self.send_message(client_sock, self.create_response())

            elif variables.ACTION in message and message[variables.ACTION] == variables.GET_CONTACTS\
                    and variables.USER in message:
                response = self.create_response(202)
                response[variables.LIST_INFO] = \
                    self.database.get_contacts(message[variables.USER][variables.ACCOUNT_NAME])
                self.logger.debug(response)
                self.send_message(client_sock, response)

            elif variables.ACTION in message and message[variables.ACTION] == variables.GET_USERS and variables.USER in message:
                response = self.create_response(202)
                response[variables.LIST_INFO] = self.database.get_users()
                self.logger.debug(response)
                self.send_message(client_sock, response)

            elif variables.ACTION in message and message[variables.ACTION] == variables.ADD_CONTACT and variables.USER in message and \
                    variables.USER_ID in message:
                self.database.add_contact(message[variables.USER][variables.ACCOUNT_NAME], message[variables.USER_ID])
                response = self.create_response(201)
                self.send_message(client_sock, response)

            elif variables.ACTION in message and message[variables.ACTION] == variables.REMOVE_CONTACT and variables.USER in message and \
                    variables.USER_ID in message:
                self.database.remove_contact(message[variables.USER][variables.ACCOUNT_NAME], message[variables.USER_ID])
                response = self.create_response(201)
                self.send_message(client_sock, response)

            elif message[variables.ACTION] == variables.EXIT:
                client_sock.close()
                self.database.user_logout(message[variables.ACCOUNT_NAME])
                del self.users_list[message[variables.USER][variables.ACCOUNT_NAME]]

            return None

        self.logger.error('message fail')
        return self.create_response('Bad request')

    def message_sender(self, user_name: str, message: dict):
        """Отправка сообщения конкретному пользователю"""
        try:
            self.send_message(self.users_list[user_name], message)
        except Exception as e:
            self.logger.info(f'Client {self.users_list[user_name].getpeername()} disconnected. 2 {e}')
            self.connected_clients.remove(self.users_list[user_name])
            del self.users_list[user_name]

    def message_sender_broadcast(self, send_queue: list, message: dict):
        """Отправка сообщений всем пользователям"""
        for waiting_client in send_queue:
            try:
                self.send_message(waiting_client, message)
            except Exception as e:
                self.logger.info(f'Client {waiting_client.getpeername()} disconnected. 1 {e}')
                self.connected_clients.remove(waiting_client)
