import logging
import threading
import time
import sys
from common import vars
from messagers.abstract_messenger import AbstractMessenger
from deorators.call_logger import CallLogger
from loggers.client_logs import server_logger



class ClientMessenger(AbstractMessenger):
    def __init__(self):
        self.socket_lock = threading.Lock()

    @CallLogger()
    def create_presence(self):
        self.logger.debug(f'Create presence message account_name: {self.account_name}')
        with self.socket_lock:
            self.send_message(self.sock, {
                vars.ACTION: vars.PRESENCE,
                vars.TIME: time.time(),
                vars.USER: {
                    vars.ACCOUNT_NAME: self.account_name
                }
            })

    def print_help(self):
        print('Поддерживаемые команды:')
        print('message - отправить сообщение. Кому и текст будет запрошены отдельно.')
        print('history - история сообщений')
        print('contacts - список контактов')
        print('edit - редактирование контактов')
        print('help - вывести подсказки по командам')
        print('exit - выход из программы')

    @CallLogger()
    def create_meesage(self):
        self.database.add_users(self.get_users())
        self.create_presence()
        self.print_help()
        while True:
            command = input('Введите команду: ')
            if command == 'exit':
                self.sock.close()
                self.logger.info('Завершение работы по команде пользователя.')
                print('Спасибо за использование нашего сервиса!')
                sys.exit(0)
            elif command == 'message':
                self.message_to_user()
            elif command == 'contacts':
                self.get_contacts()
            elif command == 'edit':
                self.edit_contacts()

    @CallLogger()
    def message_to_user(self, user_name, message_text):
        self.logger.debug(f'Create text message account_name: {self.account_name}')
        self.database.save_message(self.account_name, 'out', message_text)
        with self.socket_lock:
            self.send_message(self.sock, {
                vars.ACTION: vars.MESSAGE,
                vars.TIME: time.time(),
                vars.USER: {
                    vars.ACCOUNT_NAME: self.account_name
                },
                vars.MESSAGE_TEXT: message_text,
                vars.DESTINATION: user_name,
            })

    @CallLogger()
    def get_users(self):
        with self.socket_lock:
            self.send_message(self.sock, {
                vars.ACTION: vars.GET_USERS,
                vars.TIME: time.time(),
                vars.USER: {
                    vars.ACCOUNT_NAME: self.account_name
                },
            })
            response = self.get_message(self.sock)
            if vars.RESPONSE in response and response[vars.RESPONSE] == 202:
                return response[vars.LIST_INFO]

    @CallLogger()
    def get_contacts(self):
        self.logger.debug(f'Запрос контактов для {self.account_name}')
        with self.socket_lock:
            try:
                self.send_message(self.sock, {
                    vars.ACTION: vars.GET_CONTACTS,
                    vars.TIME: time.time(),
                    vars.USER: {
                        vars.ACCOUNT_NAME: self.account_name
                    }
                })
            except Exception as e:
                print(e)
            for contact in self.get_message(self.sock):
                self.database.add_contact(contact)

    @CallLogger()
    def edit_contacts(self):
        print('add - добавить контакт')
        print('remove - удалить контакт')
        print('back - назад')
        command = input('Введите команду: ')
        if command == 'back' or (command != 'add' and command != 'remove'):
            return

        user_name = input('Введите контакт: ')
        with self.socket_lock:
            self.send_message(self.sock, {vars.TIME: time.time(), vars.USER: {
                vars.ACCOUNT_NAME: self.account_name
            }, vars.USER_ID: user_name, vars.ACTION: vars.ADD_CONTACT if command == 'add' else vars.REMOVE_CONTACT})

    def add_contact(self, user_name):
        with self.socket_lock:
            self.send_message(self.sock, {vars.TIME: time.time(), vars.USER: {
                vars.ACCOUNT_NAME: self.account_name
            }, vars.USER_ID: user_name, vars.ACTION: vars.ADD_CONTACT})

    def remove_contact(self, user_name):
        with self.socket_lock:
            self.send_message(self.sock, {vars.TIME: time.time(), vars.USER: {
                vars.ACCOUNT_NAME: self.account_name
            }, vars.USER_ID: user_name, vars.ACTION: vars.REMOVE_CONTACT})

    @CallLogger()
    def receive_message(self):
        while True:
            time.sleep(5)
            with self.socket_lock:
                message = self.get_message(self.sock)
                if vars.RESPONSE in message and message[vars.RESPONSE] == 200:
                    self.logger.info(f'Получено сообщение 200')
                elif vars.ACTION in message and message[vars.ACTION] == vars.MESSAGE and \
                        vars.USER in message and vars.MESSAGE_TEXT in message:
                    self.database.save_message(message[vars.USER][vars.ACCOUNT_NAME], 'in', message[vars.MESSAGE_TEXT])
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
