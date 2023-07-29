import logging

logger = logging.getLogger('app.server')


class Port:
    """Дескриптор для проверки и установки порта"""
    def __set__(self, instance, value):
        if not isinstance(value, int):
            logger.critical(
                f'Тип данные не верен {value} введены тип данных {type(value)}')
            exit(1)
        if not 1023 < value < 65535:
            logger.critical(
                f'Попытка запуска сервера с указанием неподходящего порта {value}. Допустимы адреса с 1024 до 65535.')
            exit(1)
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        return int(str(instance.__dict__[self.name]))


class Host:
    """Дескриптор для проверки и установки хоста"""
    def __set__(self, instance, value):
        if not isinstance(value, str):
            logger.critical(
                f'Тип данные не верен {value} введены тип данных {type(value)}')
            exit(1)

        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        return str(instance.__dict__[self.name])
