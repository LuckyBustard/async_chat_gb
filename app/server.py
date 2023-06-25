import socket
import json
from common import vars
from common.utils import get_message, send_message, get_config_data
import logging
import loggers.server_logs

logger = logging.getLogger('app.server')


def client_presence(message: dict) -> dict:
    logger.debug(f'receive new message {message}')
    if vars.ACTION in message and message[vars.ACTION] == vars.PRESENCE and vars.TIME in message \
            and vars.USER in message and message[vars.USER][vars.ACCOUNT_NAME] == 'Guest':
        logger.debug('message ok')
        return {vars.RESPONSE: 200}
    logger.error('message fail')
    return {
        vars.RESPONSE: 400,
        vars.ERROR: 'Bad request'
    }


def main():
    listen_ip, listen_port = get_config_data()
    logger.info(f'server starting, listen ip {listen_ip}, server port {listen_port}')

    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    transport.bind((listen_ip, listen_port))
    transport.listen(vars.MAX_CONNECTIONS)

    while True:
        logger.debug('wait a message')
        client, client_address = transport.accept()
        logger.info(f'accept message from {client_address}')
        try:
            client_message = get_message(client)
            logger.debug(f'new message to send client {client_message}')
            send_message(client, client_presence(client_message))
            client.close()
        except (ValueError, json.JSONDecodeError):
            logger.error('Неверный формат сообщения')
            client.close()


if __name__ == '__main__':
    main()
