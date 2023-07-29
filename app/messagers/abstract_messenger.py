"""Модуль для отправки и получения сообщений"""
import argparse
import json
import sys
import logging
from socket import socket
from common import variables
from common.descriptors import Host, Port
import loggers.server_logs

logger = logging.getLogger('app.server')

class AbstractMessenger:
    """Класс для получения и отправки сообщения сервером и клентом"""
    listen_host = Host()
    listen_port = Port()
    account_name: str
    password: str

    def get_config_data(self, default_ip=None, default_port=None):
        """
        Конфигурирование сервера и клиента

        :param default_ip: string
        :param default_port: integer
        :returns: None
        """
        parser = argparse.ArgumentParser()
        parser.add_argument('-a', '--addr', default=default_ip or variables.DEFAULT_SERVER_IP, nargs='?')
        parser.add_argument('-p', '--port', default=default_port or variables.DEFAULT_SERVER_PORT, type=int, nargs='?')
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

        :param sock: soket
        :returns: None
        """
        response = sock.recv(variables.MAX_PACKET_LENGTH)

        if isinstance(response, bytes):
            response = json.loads(response.decode(variables.ENCODING))
            if isinstance(response, dict):
                return response
            raise ValueError
        raise ValueError

    def send_message(self, sock: socket, message: json) -> int:
        """
        Запись сообщения в сокет для отправки

        :param message: soket
        :param sock: json
        :returns: None
        """
        logger.debug(message)
        try:
            effect = sock.send(json.dumps(message).encode(variables.ENCODING))
        except Exception as e:
            logger.debug(f'{e} - error')
        return effect

    def create_response(self, status: int = 200, error: str = ''):
        """
        Создание ответа от сервера, при передаче сообщения устаналивается статус 400,
        иначе берется статус из параметра

        :param status: integer
        :param error: string
        :returns: dict
        """
        if error:
            return {
                variables.RESPONSE: 400,
                variables.ERROR: 'Bad request'
            }
        return {variables.RESPONSE: status}
