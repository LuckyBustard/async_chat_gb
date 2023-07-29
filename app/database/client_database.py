from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, Text, DateTime
from sqlalchemy.orm import mapper, sessionmaker
import datetime
import logging

logger = logging.getLogger('app.server')


class ClientStorage:
    """Класс для работы с бд на клиенте"""
    class KnownUsers:
        """Модель пользователей сервера"""
        def __init__(self, id, user):
            self.id = id
            self.username = user

    class MessageHistory:
        """Модель истории сообщений"""
        def __init__(self, contact, direction, message):
            self.id = None
            self.contact = contact
            self.direction = direction
            self.message = message
            self.date = datetime.datetime.now()

    class Contacts:
        """Модель контактов"""
        def __init__(self, contact):
            self.id = None
            self.name = contact

    def __init__(self, name):
        self.database_engine = create_engine(
            f'sqlite:///client_bases/client_{name}.db3',
            echo=False,
            pool_recycle=7200,
            connect_args={'check_same_thread': False}
        )

        self.metadata = MetaData()

        users = Table(
            'known_users', self.metadata,
            Column('uid', Integer, primary_key=True),
            Column('id', Integer),
            Column('username', String)
        )

        history = Table(
            'message_history', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('contact', String),
            Column('direction', String),
            Column('message', Text),
            Column('date', DateTime)
        )

        contacts = Table(
            'contacts', self.metadata,
            Column('uid', Integer, primary_key=True),
            Column('id', Integer),
            Column('name', String, unique=True)
        )

        self.metadata.create_all(self.database_engine)

        mapper(self.KnownUsers, users)
        mapper(self.MessageHistory, history)
        mapper(self.Contacts, contacts)

        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()

        self.session.query(self.Contacts).delete()
        self.session.commit()

    def add_contact(self, contact):
        """Добавить контакт к текущему пользователю"""
        if not self.session.query(self.Contacts).filter_by(name=contact).count():
            contact_row = self.Contacts(contact)
            self.session.add(contact_row)
            self.session.commit()

    def add_users(self, users):
        """Добавить пользователя в список известных пользователей"""
        self.session.query(self.KnownUsers).delete()
        for user in users:
            user_row = self.KnownUsers(user[0], user[1])
            self.session.add(user_row)
            self.session.commit()

    def save_message(self, contact, direction, message):
        """Сохранить сообщение в истории"""
        message_row = self.MessageHistory(contact, direction, message)
        self.session.add(message_row)
        self.session.commit()

    def get_users(self):
        """Получение списка пользоватеолей"""
        return [user[0] for user in self.session.query(self.KnownUsers.username).all()]

    def get_contacts(self):
        """Получение списка контактов"""
        return [contact[0] for contact in self.session.query(self.Contacts.name).all()]

    def get_history(self, contact):
        """Получение истории сообщений"""
        query = self.session.query(self.MessageHistory).filter_by(contact=contact)
        return [(history_row.contact, history_row.direction, history_row.message, history_row.date)
                for history_row in query.all()]

    def remove_contact(self, user):
        """удаление контакта"""
        self.session.query(self.Contacts).filter_by(name=user).delete()
