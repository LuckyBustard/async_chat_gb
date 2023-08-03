import os

from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey, DateTime
from sqlalchemy.orm import mapper, sessionmaker
from common.variables import SERVER_DATABASE
import datetime
import logging
import loggers.server_logs

logger = logging.getLogger('app.server')


class ServerStorage:
    """Класс для работы с бд на сервере"""
    class AllUsers:
        """Зарегестрированные пользователи"""
        def __init__(self, username, passwd_hash):
            self.name = username
            self.last_login = datetime.datetime.now()
            self.passwd_hash = passwd_hash
            self.pubkey = None
            self.id = None

    class ActiveUsers:
        """Авторизованные пользователи"""
        def __init__(self, user_id, ip_address, port, login_time):
            self.user = user_id
            self.ip_address = ip_address
            self.port = port
            self.login_time = login_time
            self.id = None

    class LoginHistory:
        """История авторизации"""
        def __init__(self, name, date, ip, port):
            self.id = None
            self.name = name
            self.date_time = date
            self.ip = ip
            self.port = port

    class UsersContacts:
        """Контакты пользователей"""
        def __init__(self, user, contact):
            self.id = None
            self.user = user
            self.contact = contact

    class UsersHistory:
        """Статистика пользоватлей"""
        def __init__(self, user):
            self.id = None
            self.user = user
            self.sent = 0
            self.accepted = 0

    def __init__(self):
        self.database_engine = create_engine(SERVER_DATABASE, echo=False, pool_recycle=7200,
                                             connect_args={'check_same_thread': False})

        self.metadata = MetaData()

        users_table = Table(
            'Users', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('name', String, unique=True),
            Column('passwd_hash', String),
            Column('last_login', DateTime)
        )

        active_users_table = Table(
            'Active_users', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('user', ForeignKey('Users.id'), unique=True),
            Column('ip_address', String),
            Column('port', Integer),
            Column('login_time', DateTime)
        )

        user_login_history = Table(
            'Login_history', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('name', ForeignKey('Users.id')),
            Column('date_time', DateTime),
            Column('ip', String),
            Column('port', String)
        )

        user_contacts = Table(
            'Contacts', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('user', ForeignKey('Users.id')),
            Column('contact', ForeignKey('Users.id'))
        )

        users_history = Table(
            'History', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('user', ForeignKey('Users.id')),
            Column('sent', Integer),
            Column('accepted', Integer)
        )

        self.metadata.create_all(self.database_engine)

        mapper(self.AllUsers, users_table)
        mapper(self.ActiveUsers, active_users_table)
        mapper(self.LoginHistory, user_login_history)
        mapper(self.UsersContacts, user_contacts)
        mapper(self.UsersHistory, users_history)

        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()

        self.session.query(self.ActiveUsers).delete()
        self.session.commit()

    def drop_database(self):
        self.metadata.drop_all(self.database_engine)

    def user_login(self, username, ip_address, port):
        """Авторизация пользователя"""
        logger.debug(username)
        result = self.session.query(self.AllUsers).filter_by(name=username)
        if result.count():
            user = result.first()
            user.last_login = datetime.datetime.now()
        else:
            user = self.AllUsers(username)
            self.session.add(user)
            self.session.commit()

        result = self.session.query(self.UsersHistory).filter_by(user=user.id)
        if not result.count():
            user_in_history = self.UsersHistory(user.id)
            self.session.add(user_in_history)
            self.session.commit()

        new_active_user = self.ActiveUsers(user.id, ip_address, port, datetime.datetime.now())
        self.session.add(new_active_user)

        history = self.LoginHistory(user.id, datetime.datetime.now(), ip_address, port)
        self.session.add(history)

        self.session.commit()

    def user_logout(self, username):
        """Отключение пользователя"""
        user = self.session.query(self.AllUsers).filter_by(name=username).first()
        self.session.query(self.ActiveUsers).filter_by(user=user.id).delete()
        self.session.commit()

    def users_list(self):
        """Получение списка пользоватлей сервера"""
        query = self.session.query(
            self.AllUsers.name,
            self.AllUsers.last_login,
        )
        return query.all()

    def active_users_list(self):
        """Получение списка активных пользовтаелей"""
        query = self.session.query(
            self.AllUsers.name,
            self.ActiveUsers.ip_address,
            self.ActiveUsers.port,
            self.ActiveUsers.login_time
        ).join(self.AllUsers)
        return query.all()

    def login_history(self, username=None):
        """Получение истории авторизации"""
        query = self.session.query(
            self.AllUsers.name,
            self.LoginHistory.date_time,
            self.LoginHistory.ip,
            self.LoginHistory.port
        ).join(self.AllUsers)
        if username:
            query = query.filter(self.AllUsers.name == username)
        return query.all()

    def get_contacts(self, username):
        """Получение списка контактов"""
        user = self.session.query(self.AllUsers).filter_by(name=username).first()

        query = self.session.query(self.UsersContacts, self.AllUsers.name). \
            filter_by(user=user.id). \
            join(self.AllUsers, self.UsersContacts.contact == self.AllUsers.id)

        return [contact[1] for contact in query.all()]

    def get_users(self):
        """Получение всех пользователей сервера"""
        query = self.session.query(
            self.AllUsers.id,
            self.AllUsers.name
        )
        return [tuple(row) for row in query.all()]

    def add_contact(self, user, contact):
        """Добавление контакта"""
        user = self.session.query(self.AllUsers).filter_by(name=user).first()
        contact = self.session.query(self.AllUsers).filter_by(name=contact).first()

        if not contact or self.session.query(self.UsersContacts). \
                filter_by(user=user.id, contact=contact.id).count():
            return

        contact_row = self.UsersContacts(user.id, contact.id)
        self.session.add(contact_row)
        self.session.commit()

    def remove_contact(self, user, contact):
        """Удаление контакта"""
        user = self.session.query(self.AllUsers).filter_by(name=user).first()
        contact = self.session.query(self.AllUsers).filter_by(name=contact).first()

        if not contact:
            return

        self.session.query(self.UsersContacts).filter(
            self.UsersContacts.user == user.id,
            self.UsersContacts.contact == contact.id
        ).delete()
        self.session.commit()

    def process_message(self, sender, recipient):
        """Отправка сообщения от пользователя к пользователю"""
        sender = self.session.query(self.AllUsers).filter_by(name=sender).first().id
        recipient = self.session.query(self.AllUsers).filter_by(name=recipient).first().id
        sender_row = self.session.query(self.UsersHistory).filter_by(user=sender).first()
        sender_row.sent += 1
        self.session.commit()
        recipient_row = self.session.query(self.UsersHistory).filter_by(user=recipient).first()
        recipient_row.accepted += 1
        self.session.commit()

    def message_history(self):
        """Получение истории сообщений"""
        query = self.session.query(
            self.AllUsers.name,
            self.AllUsers.last_login,
            self.UsersHistory.sent,
            self.UsersHistory.accepted
        ).join(self.AllUsers)
        return query.all()

    def get_user_salt(self, username):
        """Получение пользовательской соли"""
        result = self.session.query(self.AllUsers).filter_by(name=username)
        if result.count():
            return result.first().salt
        return None

    def register_user(self, username, passwd_hash):
        """Регистрация пользователя"""
        user = self.AllUsers(username, passwd_hash)
        self.session.add(user)
        self.session.commit()

    def check_user(self, username):
        """Проверька существования пользователя"""
        return self.session.query(self.AllUsers).filter_by(name=username).count() > 0

    def get_hash(self, username):
        """Получение хешированного паролья пользователя"""
        user = self.session.query(self.AllUsers).filter_by(name=username).first()
        return user.passwd_hash
