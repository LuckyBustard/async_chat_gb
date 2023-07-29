import os
import sys
import unittest

sys.path.append(os.path.join(os.getcwd(), '..'))

from server import client_presence
from common import variables


class TestServer(unittest.TestCase):
    ok_data = {variables.RESPONSE: 200}
    err_data = {
        variables.RESPONSE: 400,
        variables.ERROR: 'Bad request'
    }

    def test_no_action(self):
        self.assertEqual(client_presence({
            variables.TIME: '0',
            variables.USER: {
                variables.ACCOUNT_NAME: 'Guest'
            }
        }), self.err_data)

    def test_no_time(self):
        self.assertEqual(client_presence({
            variables.ACTION: variables.PRESENCE,
            variables.USER: {
                variables.ACCOUNT_NAME: 'Guest'
            }
        }), self.err_data)

    def test_no_user(self):
        self.assertEqual(client_presence({
            variables.ACTION: variables.PRESENCE,
            variables.TIME: '0',
        }), self.err_data)

    def test_wrong_user(self):
        self.assertEqual(client_presence({
            variables.ACTION: variables.PRESENCE,
            variables.TIME: '0',
            variables.USER: {
                variables.ACCOUNT_NAME: 'Admin'
            }
        }), self.err_data)

    def test_ok(self):
        self.assertEqual(client_presence({
            variables.ACTION: variables.PRESENCE,
            variables.TIME: '0',
            variables.USER: {
                variables.ACCOUNT_NAME: 'Guest'
            }
        }), self.ok_data)


if __name__ == '__main__':
    unittest.main()
