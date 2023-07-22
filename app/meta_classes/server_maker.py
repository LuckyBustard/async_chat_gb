import dis
import logging
import loggers.server_logs


logger = logging.getLogger('app.server')


class ServerMaker(type):
    def __init__(self, clsname, bases, clsdict):
        globals = []
        for func in clsdict:
            try:
                ret = dis.get_instructions(clsdict[func])
            except TypeError:
                pass
            else:
                for i in ret:
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in globals:
                            globals.append(i.argval)
        if 'connect' in globals:
            raise TypeError('Использование метода connect недопустимо в серверном классе')
        if not ('SOCK_STREAM' in globals and 'AF_INET' in globals):
            raise TypeError('Некорректная инициализация сокета.')
        super().__init__(clsname, bases, clsdict)
