import socket
import time
from common import vars
from common.utils import get_message, send_message, get_config_data, create_response
import logging
import select
import loggers.server_logs
from deorators.call_logger import CallLogger

logger = logging.getLogger('app.server')


@CallLogger()
def process_client_message(client_sock: socket, wait_messages: list, users: dict):
    """
    Получение сообщения от клиента и постановка его в очередь сообщений

    :param users:
    :param client_sock:
    :param wait_messages:
    :return:
    """
    message = get_message(client_sock)

    logger.debug(f'receive new message {message}')
    if vars.ACTION in message and vars.TIME in message and vars.USER in message:
        # Страшно переходить на версию 3.10 но очень хочется матч кейс
        if message[vars.ACTION] == vars.PRESENCE:
            if message[vars.USER][vars.ACCOUNT_NAME] not in users.keys():
                users[message[vars.USER][vars.ACCOUNT_NAME]] = client_sock
                send_message(client_sock, create_response())
            else:
                send_message(client_sock, create_response('Имя пользователя уже занято.'))
                client_sock.close()

        elif message[vars.ACTION] == vars.MESSAGE and vars.DESTINATION in message:
            logger.debug('message ok')
            wait_messages.append((message[vars.USER], message[vars.MESSAGE_TEXT], message[vars.DESTINATION]))
            send_message(client_sock, create_response())

        elif message[vars.ACTION] == vars.EXIT:
            client_sock.close()
            del users[message[vars.USER][vars.ACCOUNT_NAME]]

        return

    logger.error('message fail')
    return create_response('Bad request')


@CallLogger()
def message_sender(user_name: str, message: dict, users_list: dict, connected_clients: list):
    try:
        send_message(users_list[user_name], message)
    except Exception as e:
        logger.info(f'Client {users_list[user_name].getpeername()} disconnected. 2 {e}')
        connected_clients.remove(users_list[user_name])
        del users_list[user_name]


@CallLogger()
def message_sender_broadcast(send_queue: list, message: dict, connected_clients: list):
    for waiting_client in send_queue:
        try:
            send_message(waiting_client, message)
        except Exception as e:
            logger.info(f'Client {waiting_client.getpeername()} disconnected. 1 {e}')
            connected_clients.remove(waiting_client)


def main():
    listen_ip, listen_port, _ = get_config_data()
    logger.info(f'server starting, listen ip {listen_ip}, server port {listen_port}')

    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    transport.bind((listen_ip, listen_port))
    transport.listen(vars.MAX_CONNECTIONS)
    transport.settimeout(0.5)

    connected_clients = []
    waiting_messages = []
    users_list = dict()

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
                    process_client_message(waiting_messanger, waiting_messages, users_list)
                except Exception as e:
                    logger.info(f'Client {waiting_messanger.getpeername()} disconnected. {e}')
                    connected_clients.remove(waiting_messanger)

        if waiting_messages and send_queue:
            for wait_message in waiting_messages:
                user_name = wait_message[2]
                message = {
                    vars.ACTION: vars.MESSAGE,
                    vars.USER: wait_message[0],
                    vars.TIME: time.time(),
                    vars.MESSAGE_TEXT: wait_message[1]
                }
                waiting_messages.remove(wait_message)

                if wait_message[2] == vars.DESTINATION_ALL:
                    message_sender_broadcast(send_queue, message, connected_clients)
                else:
                    message_sender(user_name, message, users_list, connected_clients)


if __name__ == '__main__':
    main()
