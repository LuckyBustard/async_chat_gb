import binascii
import hmac
import os
from socket import socket
from common import vars
from deorators.login_required import login_required
from messagers.abstract_messenger import AbstractMessenger
from deorators.call_logger import CallLogger


class ServerMessenger(AbstractMessenger):
    @CallLogger()
    def authorise_user(self, client_socket, message):
        message_auth = self.create_response(511)
        random_str = binascii.hexlify(os.urandom(64))
        message_auth[vars.DATA] = random_str.decode('ascii')
        hash = hmac.new(self.database.get_hash(message[vars.USER][vars.ACCOUNT_NAME]), random_str, 'MD5')
        digest = hash.digest()

        self.send_message(client_socket, message_auth)
        answer = self.get_message(client_socket)
        client_digest = binascii.a2b_base64(answer[vars.DATA])

        if vars.RESPONSE in answer and answer[vars.RESPONSE] == 511 and hmac.compare_digest(
                digest, client_digest):
            client_ip, client_port = client_socket.getpeername()
            self.database.user_login(
            message[vars.USER][vars.ACCOUNT_NAME],
            client_ip,
            client_port,
            message[vars.USER][vars.PUBLIC_KEY])

            self.users_list[message[vars.USER][vars.ACCOUNT_NAME]] = client_socket
            self.send_message(client_socket, self.create_response())
        else:
            try:
                self.send_message(client_socket, self.create_response(400, 'Неверный пароль'))
            except OSError:
                pass
            self.clients.remove(client_socket)
            client_socket.close()

    @login_required()
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
                if message[vars.USER][vars.ACCOUNT_NAME] not in self.users_list.keys() \
                        and self.database.check_user(message[vars.USER][vars.ACCOUNT_NAME]):
                    self.authorise_user(client_sock, message)
                else:
                    self.send_message(client_sock, self.create_response('Имя пользователя уже занято.'))
                    client_sock.close()

            elif message[vars.ACTION] == vars.MESSAGE and vars.DESTINATION in message:
                self.waiting_messages.append(
                    (message[vars.USER], message[vars.MESSAGE_TEXT], message[vars.DESTINATION]))
                self.database.process_message(message[vars.USER], message[vars.DESTINATION])
                self.send_message(client_sock, self.create_response())

            elif vars.ACTION in message and message[vars.ACTION] == vars.GET_CONTACTS and vars.USER in message:
                response = self.create_response(202)
                response[vars.LIST_INFO] = self.database.get_contacts(message[vars.USER][vars.ACCOUNT_NAME])
                self.logger.debug(response)
                self.send_message(client_sock, response)

            elif vars.ACTION in message and message[vars.ACTION] == vars.GET_USERS and vars.USER in message:
                response = self.create_response(202)
                response[vars.LIST_INFO] = self.database.get_users()
                self.logger.debug(response)
                self.send_message(client_sock, response)

            elif vars.ACTION in message and message[vars.ACTION] == vars.ADD_CONTACT and vars.USER in message and \
                    vars.USER_ID in message:
                self.database.add_contact(message[vars.USER][vars.ACCOUNT_NAME], message[vars.USER_ID])
                response = self.create_response(201)
                self.send_message(client_sock, response)

            elif vars.ACTION in message and message[vars.ACTION] == vars.REMOVE_CONTACT and vars.USER in message and \
                    vars.USER_ID in message:
                self.database.remove_contact(message[vars.USER][vars.ACCOUNT_NAME], message[vars.USER_ID])
                response = self.create_response(201)
                self.send_message(client_sock, response)

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
