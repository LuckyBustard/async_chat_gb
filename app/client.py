import socket
import json
import time

from common import vars
from common.utils import get_message, send_message, get_config_data


def create_presence(account_name='Guest') -> dict:
    return {
        vars.ACTION: vars.PRESENCE,
        vars.TIME: time.time(),
        vars.USER: {
            vars.ACCOUNT_NAME: account_name
        }
    }


def process_answer(message: dict):
    if vars.RESPONSE in message:
        if message[vars.RESPONSE] == 200:
            return '200: OK'
        return f'400: {message[vars.ERROR]}'
    raise ValueError


def main():
    listen_ip, listen_port = get_config_data()

    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.connect((listen_ip, listen_port))

    while True:
        try:
            send_message(serverSocket, create_presence())
            print(process_answer(get_message(serverSocket)))

            send_message(serverSocket, create_presence('Admin'))
            print(process_answer(get_message(serverSocket)))

            serverSocket.close()

        except (ValueError, json.JSONDecodeError):
            print('Неверный формат сообщения')


if __name__ == '__main__':
    main()
