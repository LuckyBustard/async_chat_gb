import threading
import time
import sys
import logging
from common.meta_classes import ClientMaker
from socket import socket, AF_INET, SOCK_STREAM
from common import vars
from common.abstract_messenger import AbstractMessenger
from deorators.call_logger import CallLogger
import loggers.client_logs


class Client(AbstractMessenger, metaclass=ClientMaker):
    def __init__(self):
        self.logger = logging.getLogger('app.client')
        self.get_config_data()
        self.logger.info('connected to server')

    def connect(self):
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.sock.connect((self.listen_host, self.listen_port))

    @CallLogger()
    def create_presence(self):
        self.logger.debug(f'Create presence message account_name: {self.account_name}')
        self.send_message(self.sock, {
            vars.ACTION: vars.PRESENCE,
            vars.TIME: time.time(),
            vars.USER: {
                vars.ACCOUNT_NAME: self.account_name
            }
        })

    @CallLogger()
    def create_meesage(self):
        while True:
            destination = input('Введите пользователя или all для отправки или \'@q\' для завершения работы: ')
            message_text = input('Введите сообщение для отправки или \'@q\' для завершения работы: ')
            if message_text == '@q':
                self.sock.close()
                self.logger.info('Завершение работы по команде пользователя.')
                print('Спасибо за использование нашего сервиса!')
                sys.exit(0)
            self.logger.debug(f'Create text message account_name: {self.account_name}')
            self.send_message(self.sock, {
                vars.ACTION: vars.MESSAGE,
                vars.TIME: time.time(),
                vars.USER: {
                    vars.ACCOUNT_NAME: self.account_name
                },
                vars.MESSAGE_TEXT: message_text,
                vars.DESTINATION: destination,
            })

    @CallLogger()
    def receive_message(self):
        while True:
            message = self.get_message(self.sock)
            if vars.RESPONSE in message and message[vars.RESPONSE] == 200:
                self.logger.info(f'Получено сообщение 200')
            elif vars.ACTION in message and message[vars.ACTION] == vars.MESSAGE and \
                    vars.USER in message and vars.MESSAGE_TEXT in message:
                self.logger.info(
                    f'Получено сообщение от пользователя {message[vars.USER][vars.ACCOUNT_NAME]}: {message[vars.MESSAGE_TEXT]}')
            else:
                self.logger.error(f'Получено некорректное сообщение с сервера: {message}')

    @CallLogger()
    def process_answer(self, message: dict):
        self.logger.debug(f'receive new message {message}')
        if vars.RESPONSE in message:
            if message[vars.RESPONSE] == 200:
                self.logger.debug('message ok')
                return '200: OK'
            self.logger.error('message fail')
            return f'400: {message[vars.ERROR]}'
        raise ValueError

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
