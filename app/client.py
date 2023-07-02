import socket
import time
import sys
from common import vars
from common.utils import get_message, send_message, get_config_data
import logging
import loggers.client_logs
from deorators.call_logger import CallLogger


logger = logging.getLogger('app.client')


@CallLogger()
def create_presence(sock: socket, account_name='Guest'):
    logger.debug(f'Create presence message account_name: {account_name}')
    send_message(sock, {
        vars.ACTION: vars.PRESENCE,
        vars.TIME: time.time(),
        vars.USER: {
            vars.ACCOUNT_NAME: account_name
        }
    })


@CallLogger()
def create_meesage(sock, account_name='Guest'):
    message_text = input('Введите сообщение для отправки или \'@q\' для завершения работы: ')
    if message_text == '@q':
        sock.close()
        logger.info('Завершение работы по команде пользователя.')
        print('Спасибо за использование нашего сервиса!')
        sys.exit(0)
    logger.debug(f'Create text message account_name: {account_name}')
    send_message(sock, {
        vars.ACTION: vars.MESSAGE,
        vars.TIME: time.time(),
        vars.USER: account_name,
        vars.MESSAGE_TEXT: message_text
    })


@CallLogger()
def receive_message(sock: socket):
    message = get_message(sock)
    logger.debug(f'{message}')
    if vars.ACTION in message and message[vars.ACTION] == vars.MESSAGE and \
            vars.USER in message and vars.MESSAGE_TEXT in message:
        logger.info(f'Получено сообщение от пользователя {message[vars.USER]}: {message[vars.MESSAGE_TEXT]}')
    else:
        logger.error(f'Получено некорректное сообщение с сервера: {message}')

@CallLogger()
def process_answer(message: dict):
    logger.debug(f'receive new message {message}')
    if vars.RESPONSE in message:
        if message[vars.RESPONSE] == 200:
            logger.debug('message ok')
            return '200: OK'
        logger.error('message fail')
        return f'400: {message[vars.ERROR]}'
    raise ValueError


def main():
    listen_ip, listen_port, client_mode = get_config_data()
    logger.info(f'connecting to server, server ip {listen_ip}, server port {listen_port}')

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((listen_ip, listen_port))
    logger.info('connected to server')
    create_presence(client_socket)
    logger.debug(f'answer from server: {process_answer(get_message(client_socket))}')

    if client_mode == 'send':
        logger.info('Режим работы - отправка сообщений.')
    else:
        logger.info('Режим работы - приём сообщений.')

    while True:
        try:
            if client_mode == 'send':
                create_meesage(client_socket)
            if client_mode == 'listen':
                receive_message(client_socket)
        except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
            logger.error(f'Соединение с сервером {listen_ip} было потеряно.')
            sys.exit(1)


if __name__ == '__main__':
    main()
