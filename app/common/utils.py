import argparse
import json
import logging
import sys
from socket import socket
from common import vars
from loggers.server_logs import server_logger

logger = logging.getLogger('app.server')


def get_message(sock: socket) -> dict:
    """
    Чтение из сокета сообщения и декодирование

    :param sock:
    :return:
    """
    response = sock.recv(vars.MAX_PACKET_LENGTH)

    if isinstance(response, bytes):
        response = json.loads(response.decode(vars.ENCODING))
        if isinstance(response, dict):
            return response
        raise ValueError
    raise ValueError


def send_message(sock: socket, message: json) -> int:
    """
    Запись сообщения в сокет для отправки

    :param message:
    :param sock:
    :return:
    """
    try:
        effect = sock.send(json.dumps(message).encode(vars.ENCODING))
    except Exception as e:
        logger.debug(f'{e} - error')
    return effect


def get_config_data():
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--addr', default=vars.DEFAULT_SERVER_IP, nargs='?')
    parser.add_argument('-p', '--port', default=vars.DEFAULT_SERVER_PORT, type=int, nargs='?')
    parser.add_argument('-n', '--name', default='listen', nargs='?')
    args = parser.parse_args(sys.argv[1:])
    listen_ip = args.addr
    listen_port = args.port
    client_mode = args.name

    if 65535 < listen_port < 1024:
        raise ValueError

    return listen_ip, listen_port, str(client_mode)


def create_response(error: str = ''):
    if error:
        return {
            vars.RESPONSE: 400,
            vars.ERROR: 'Bad request'
        }
    return {vars.RESPONSE: 200}