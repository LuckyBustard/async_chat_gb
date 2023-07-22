import os
import sys
import unittest

sys.path.append(os.path.join(os.getcwd(), '..'))

from database.server_database import ServerStorage


class TestDatabase(unittest.TestCase):
    storage = None

    @classmethod
    def setUpClass(cls):
        cls.storage = ServerStorage()

    @classmethod
    def tearDownClass(cls):
        cls.storage.drop_database()

    def setUp(self):
        self.storage.user_login('client_1', '192.168.1.4', 8888)
        self.storage.user_login('client_2', '192.168.1.5', 7777)

    def tearDown(self):
        self.storage.user_logout('client_1')
        self.storage.user_logout('client_2')

    def test_users_list(self):
        users_list = self.storage.active_users_list()
        self.assertEqual(users_list[0][0], 'client_1')
        self.assertEqual(users_list[0][1], '192.168.1.4')
        self.assertEqual(users_list[0][2], 8888)
        self.assertEqual(users_list[1][0], 'client_2')
        self.assertEqual(users_list[1][1], '192.168.1.5')
        self.assertEqual(users_list[1][2], 7777)

    def test_user_logout(self):
        self.storage.user_logout('client_1')
        users_list = self.storage.active_users_list()
        print(users_list)
        self.assertEqual(users_list[0][0], 'client_2')
        self.assertEqual(users_list[0][1], '192.168.1.5')
        self.assertEqual(users_list[0][2], 7777)

    def test_history(self):
        history = self.storage.login_history('client_1')
        self.assertEqual(history[0][0], 'client_1')
        self.assertEqual(history[0][1], '192.168.1.4')
        self.assertEqual(history[0][2], 8888)


if __name__ == '__main__':
    unittest.main()
