"""Логирование вызова функции"""
import inspect
import logging
import sys
import traceback
import loggers.client_logs
import loggers.server_logs


logger = logging.getLogger('app.' + ('server' if sys.argv[0].find('client') == -1 else 'client'))


class CallLogger:
    def __int__(self):
        pass

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            res = func(*args, **kwargs)
            logger.debug(
                f'Функция: {func.__name__} параметры: {args}, {kwargs} | '
                f'модуль: {func.__module__} | '
                f'Вызвана в: {inspect.stack()[1][3]} |', stacklevel=2
            )

            return res

        return wrapper
