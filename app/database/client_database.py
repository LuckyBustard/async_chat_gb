from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, Text, DateTime
from sqlalchemy.orm import mapper, sessionmaker
import datetime
import logging

logger = logging.getLogger('app.server')


class ClientStorage:
    class KnownUsers:
        def __init__(self, id, user):
            self.id = id
            self.username = user

    class MessageHistory:
        def __init__(self, from_user, to_user, message):
            self.id = None
            self.from_user = from_user
            self.to_user = to_user
            self.message = message
            self.date = datetime.datetime.now()

    class Contacts:
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
            Column('from_user', String),
            Column('to_user', String),
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
        if not self.session.query(self.Contacts).filter_by(name=contact).count():
            contact_row = self.Contacts(contact)
            self.session.add(contact_row)
            self.session.commit()

    def add_users(self, users):
        self.session.query(self.KnownUsers).delete()
        for user in users:
            user_row = self.KnownUsers(user[0], user[1])
            self.session.add(user_row)
            self.session.commit()

    def save_message(self, from_user, to_user, message):
        message_row = self.MessageHistory(from_user, to_user, message)
        self.session.add(message_row)
        self.session.commit()
