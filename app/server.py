import socket
import json
from common import vars
from common.utils import get_message, send_message, get_config_data


def client_presence(message: dict) -> dict:
    if vars.ACTION in message and message[vars.ACTION] == vars.PRESENCE and vars.TIME in message \
            and vars.USER in message and message[vars.USER][vars.ACCOUNT_NAME] == 'Guest':
        return {vars.RESPONSE: 200}
    return {
        vars.RESPONSE: 400,
        vars.ERROR: 'Bad request'
    }


def main():
    listen_ip, listen_port = get_config_data()

    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    transport.bind((listen_ip, listen_port))
    transport.listen(vars.MAX_CONNECTIONS)

    while True:
        client, client_address = transport.accept()
        try:
            client_message = get_message(client)
            print(client_message)
            send_message(client, client_presence(client_message))
            client.close()
        except (ValueError, json.JSONDecodeError):
            print('Неверный формат сообщения')
            client.close()


if __name__ == '__main__':
    print('1')
    main()
