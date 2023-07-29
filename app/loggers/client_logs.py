"""Логгер клиентского приложения"""

import logging
import os
from logging import handlers

log_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'logs/client.log')
server_logger = logging.getLogger('app.client')

formatter = logging.Formatter("%(asctime)-30s %(levelname)-10s %(module)s %(message)s ")

file_handler = handlers.TimedRotatingFileHandler(log_path, when='midnight', interval=1, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

server_logger.addHandler(file_handler)
server_logger.setLevel(logging.DEBUG)

console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
console.setFormatter(formatter)

server_logger.addHandler(console)
