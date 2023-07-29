"""Общие переменные"""
DEFAULT_SERVER_IP = '0.0.0.0'
DEFAULT_SERVER_PORT = 7777

MAX_CONNECTIONS = 5
MAX_PACKET_LENGTH = 1024

ENCODING = 'utf-8'

ACTION = 'action'
TIME = 'time'
USER = 'user'
ACCOUNT_NAME = 'account_name'

PRESENCE = 'presence'
RESPONSE = 'response'
MESSAGE = 'message'
MESSAGE_TEXT = 'message_text'
DESTINATION = 'destination'
DESTINATION_ALL = 'all'
GET_CONTACTS = 'get_contacts'
ADD_CONTACT = 'add_contact'
REMOVE_CONTACT = 'remove_contact'
GET_USERS = 'get_users'
USER_ID = 'user_id'
LIST_INFO = 'list_info'
ERROR = 'error'
EXIT = 'exit'
DATA = 'bin'
PUBLIC_KEY = 'pubkey'
PUBLIC_KEY_REQUEST = 'pubkey_need'

SERVER_DATABASE = 'sqlite:///server_base.db3'
