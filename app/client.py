import socket
import json
import time

from common import vars
from common.utils import get_message, send_message, get_config_data
import logging
import loggers.client_logs
from deorators.call_logger import CallLogger


logger = logging.getLogger('app.client')


@CallLogger()
def create_presence(account_name='Guest') -> dict:
    logger.debug(f'Create presence message account_name: {account_name}')
    return {
        vars.ACTION: vars.PRESENCE,
        vars.TIME: time.time(),
        vars.USER: {
            vars.ACCOUNT_NAME: account_name
        }
    }


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
    listen_ip, listen_port = get_config_data()
    logger.info(f'connecting to server, server ip {listen_ip}, server port {listen_port}')

    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.connect((listen_ip, listen_port))
    logger.info('connected to server')

    while True:
        try:
            send_message(serverSocket, create_presence())
            logger.debug(f'answer from server: {process_answer(get_message(serverSocket))}')

            send_message(serverSocket, create_presence('Admin'))
            logger.debug(f'answer from server: {process_answer(get_message(serverSocket))}')

            serverSocket.close()

        except (ValueError, json.JSONDecodeError):
            logger.error('Неверный формат сообщения')


if __name__ == '__main__':
    main()
