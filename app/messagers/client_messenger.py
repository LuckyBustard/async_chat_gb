import binascii
import hashlib
import hmac
import logging
import threading
import time
import sys
from common import variables
from messagers.abstract_messenger import AbstractMessenger
from deсorators.call_logger import CallLogger
from loggers.client_logs import server_logger


class ClientMessenger(AbstractMessenger):
    """Класс месеннджера для сервера. Отвечает за генерацию, авторизацию, отправку с получением сообщений от сервера"""
    def __init__(self):
        self.socket_lock = threading.Lock()

    def create_presence(self):
        """Приветствие и авторизация на сервере"""
        self.logger.debug(f'Create presence message account_name: {self.account_name}')

        passwd_bytes = self.password.encode('utf-8')
        salt = self.account_name.lower().encode('utf-8')
        passwd_hash = hashlib.pbkdf2_hmac('sha512', passwd_bytes, salt, 10000)
        passwd_hash_string = binascii.hexlify(passwd_hash)

        with self.socket_lock:
            self.send_message(self.sock, {
                variables.ACTION: variables.PRESENCE,
                variables.TIME: time.time(),
                variables.USER: {
                    variables.ACCOUNT_NAME: self.account_name
                }
            })
            answer = self.get_message(self.sock)
            if answer[variables.RESPONSE] == 511:
                ans_data = answer[variables.DATA]
                hash = hmac.new(passwd_hash_string, ans_data.encode('utf-8'), 'MD5')
                digest = hash.digest()
                my_ans = self.create_response(511)
                my_ans[variables.DATA] = binascii.b2a_base64(digest).decode('ascii')
                self.send_message(self.sock, my_ans)

    def print_help(self):
        print('Поддерживаемые команды:')
        print('message - отправить сообщение. Кому и текст будет запрошены отдельно.')
        print('history - история сообщений')
        print('contacts - список контактов')
        print('edit - редактирование контактов')
        print('help - вывести подсказки по командам')
        print('exit - выход из программы')

    def create_meesage(self):
        """Метод создания сообщений к серверу: отправка сообщений, получение списка контактов"""
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

    def message_to_user(self, user_name, message_text):
        """Отправка сообщения конкретному пользователю"""
        self.logger.debug(f'Create text message account_name: {self.account_name}')
        self.database.save_message(self.account_name, 'out', message_text)
        with self.socket_lock:
            self.send_message(self.sock, {
                variables.ACTION: variables.MESSAGE,
                variables.TIME: time.time(),
                variables.USER: {
                    variables.ACCOUNT_NAME: self.account_name
                },
                variables.MESSAGE_TEXT: message_text,
                variables.DESTINATION: user_name,
            })

    def get_users(self):
        """Получение списка пользоватлей с сервера"""
        with self.socket_lock:
            self.send_message(self.sock, {
                variables.ACTION: variables.GET_USERS,
                variables.TIME: time.time(),
                variables.USER: {
                    variables.ACCOUNT_NAME: self.account_name
                },
            })
            response = self.get_message(self.sock)
            if variables.RESPONSE in response and response[variables.RESPONSE] == 202:
                return response[variables.LIST_INFO]

    def get_contacts(self):
        """Запрос списка контактов"""
        self.logger.debug(f'Запрос контактов для {self.account_name}')
        with self.socket_lock:
            try:
                self.send_message(self.sock, {
                    variables.ACTION: variables.GET_CONTACTS,
                    variables.TIME: time.time(),
                    variables.USER: {
                        variables.ACCOUNT_NAME: self.account_name
                    }
                })
            except Exception as e:
                print(e)
            for contact in self.get_message(self.sock):
                self.database.add_contact(contact)

    def edit_contacts(self):
        """Изменение списка контактов: удаление или добавление"""
        print('add - добавить контакт')
        print('remove - удалить контакт')
        print('back - назад')
        command = input('Введите команду: ')
        if command == 'back' or (command != 'add' and command != 'remove'):
            return

        user_name = input('Введите контакт: ')
        with self.socket_lock:
            self.send_message(self.sock, {variables.TIME: time.time(), variables.USER: {
                variables.ACCOUNT_NAME: self.account_name
            }, variables.USER_ID: user_name, variables.ACTION: variables.ADD_CONTACT if command == 'add' else variables.REMOVE_CONTACT})

    def add_contact(self, user_name):
        """Добавление контакта"""
        with self.socket_lock:
            self.send_message(self.sock, {variables.TIME: time.time(), variables.USER: {
                variables.ACCOUNT_NAME: self.account_name
            }, variables.USER_ID: user_name, variables.ACTION: variables.ADD_CONTACT})

    def remove_contact(self, user_name):
        """Удаление контакта"""
        with self.socket_lock:
            self.send_message(self.sock, {variables.TIME: time.time(), variables.USER: {
                variables.ACCOUNT_NAME: self.account_name
            }, variables.USER_ID: user_name, variables.ACTION: variables.REMOVE_CONTACT})

    def receive_message(self):
        """Метод для получение сообщений от сервера"""
        while True:
            time.sleep(5)
            with self.socket_lock:
                message = self.get_message(self.sock)
                if variables.RESPONSE in message and message[variables.RESPONSE] == 200:
                    self.logger.info(f'Получено сообщение 200')
                elif variables.ACTION in message and message[variables.ACTION] == variables.MESSAGE and \
                        variables.USER in message and variables.MESSAGE_TEXT in message:
                    self.database.save_message(message[variables.USER][variables.ACCOUNT_NAME], 'in', message[variables.MESSAGE_TEXT])
                    self.logger.info(
                        f'Получено сообщение от пользователя {message[variables.USER][variables.ACCOUNT_NAME]}: {message[variables.MESSAGE_TEXT]}')
                else:
                    self.logger.error(f'Получено некорректное сообщение с сервера: {message}')

    def process_answer(self, message: dict):
        """Метод для проверки корректности сообщенияы"""
        self.logger.debug(f'receive new message {message}')
        if variables.RESPONSE in message:
            if message[variables.RESPONSE] == 200:
                self.logger.debug('message ok')
                return '200: OK'
            self.logger.error('message fail')
            return f'400: {message[variables.ERROR]}'
        raise ValueError
