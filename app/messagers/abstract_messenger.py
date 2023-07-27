import argparse
import json
import sys
import logging
from socket import socket
from common import vars
from common.descriptors import Host, Port
import loggers.server_logs

logger = logging.getLogger('app.server')


class AbstractMessenger:
    listen_host = Host()
    listen_port = Port()
    account_name: str
    password: str

    def get_config_data(self, default_ip=None, default_port=None):
        parser = argparse.ArgumentParser()
        parser.add_argument('-a', '--addr', default=default_ip or vars.DEFAULT_SERVER_IP, nargs='?')
        parser.add_argument('-p', '--port', default=default_port or vars.DEFAULT_SERVER_PORT, type=int, nargs='?')
        parser.add_argument('-n', '--name', default='listen', nargs='?')
        parser.add_argument('-P', '--password', default='', nargs='?')
        args = parser.parse_args(sys.argv[1:])
        self.listen_host = args.addr
        self.listen_port = int(args.port)
        self.account_name = args.name
        self.password = args.password

    def get_message(self, sock: socket) -> dict:
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

    def send_message(self, sock: socket, message: json) -> int:
        """
        Запись сообщения в сокет для отправки

        :param message:
        :param sock:
        :return:
        """
        logger.debug(message)
        try:
            effect = sock.send(json.dumps(message).encode(vars.ENCODING))
        except Exception as e:
            logger.debug(f'{e} - error')
        return effect

    def create_response(self, status: int = 200, error: str = ''):
        if error:
            return {
                vars.RESPONSE: 400,
                vars.ERROR: 'Bad request'
            }
        return {vars.RESPONSE: status}
