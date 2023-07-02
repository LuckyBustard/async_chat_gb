import socket
import time
from common import vars
from common.utils import get_message, send_message, get_config_data
import logging
import select
import loggers.server_logs
from deorators.call_logger import CallLogger

logger = logging.getLogger('app.server')


@CallLogger()
def process_client_message(client_sock: socket, wait_messages: list):
    """
    Получение сообщения от клиента и постановка его в очередь сообщений

    :param client_sock:
    :param wait_messages:
    :return:
    """
    message = get_message(client_sock)

    logger.debug(f'receive new message {message}')
    if vars.ACTION in message and message[vars.ACTION] == vars.PRESENCE \
            and vars.TIME in message and vars.USER in message:
        logger.debug('message ok')
        send_message(client_sock, {vars.RESPONSE: 200})
        return

    if vars.ACTION in message and message[vars.ACTION] == vars.MESSAGE \
            and vars.TIME in message and vars.USER in message:
        logger.debug('message ok')
        wait_messages.append((message[vars.USER], message[vars.MESSAGE_TEXT]))
        send_message(client_sock, {vars.RESPONSE: 200})
        return

    logger.error('message fail')
    return {
        vars.RESPONSE: 400,
        vars.ERROR: 'Bad request'
    }


def main():
    listen_ip, listen_port, _ = get_config_data()
    logger.info(f'server starting, listen ip {listen_ip}, server port {listen_port}')

    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    transport.bind((listen_ip, listen_port))
    transport.listen(vars.MAX_CONNECTIONS)
    transport.settimeout(0.5)

    connected_clients = []
    waiting_messages = []

    while True:
        try:
            client, client_address = transport.accept()
        except OSError:
            pass
        else:
            connected_clients.append(client)
            logger.info(f'accept connection from {client_address}')

        recv_queue = []
        send_queue = []
        err_lst = []
        try:
            if connected_clients:
                recv_queue, send_queue, err_lst = select.select(connected_clients, connected_clients, [], 0)
        except OSError:
            pass

        if recv_queue:
            for waiting_messanger in recv_queue:
                try:
                    process_client_message(waiting_messanger, waiting_messages)
                except:
                    logger.info(f'Client {waiting_messanger.getpeername()} disconnected.')
                    connected_clients.remove(waiting_messanger)

        if waiting_messages and send_queue:
            for wait_message in waiting_messages:
                message = {
                    vars.ACTION: vars.MESSAGE,
                    vars.USER: wait_message[0],
                    vars.TIME: time.time(),
                    vars.MESSAGE_TEXT: wait_message[1]
                }
                waiting_messages.remove(wait_message)

                for waiting_client in send_queue:
                    try:
                        send_message(waiting_client, message)
                    except:
                        logger.info(f'Client {waiting_messanger.getpeername()} disconnected.')
                        connected_clients.remove(waiting_client)


if __name__ == '__main__':
    main()
