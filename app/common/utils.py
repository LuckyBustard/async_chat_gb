import json
import sys
from socket import socket
from common import vars


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

    return sock.send(json.dumps(message).encode(vars.ENCODING))


def get_config_data():
    listen_ip = vars.DEFAULT_SERVER_IP
    listen_port = vars.DEFAULT_SERVER_PORT

    try:
        if '-p' in sys.argv:
            listen_port = int(sys.argv[sys.argv.index('-p') + 1])
            if 65535 < listen_port < 1024:
                raise ValueError
    except IndexError:
        print('После параметра не указан порт')
        sys.exit(1)
    except ValueError:
        print('Значение порта указано вне диапозона')
        sys.exit(1)

    try:
        if '-a' in sys.argv:
            listen_port = sys.argv[sys.argv.index('-a') + 1]
    except IndexError:
        print('После параметра не указан ip адрес')
        sys.exit(1)

    return listen_ip, listen_port
