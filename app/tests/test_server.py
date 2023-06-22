import os
import sys
import unittest

sys.path.append(os.path.join(os.getcwd(), '..'))

from server import client_presence
from common import vars


class TestServer(unittest.TestCase):
    ok_data = {vars.RESPONSE: 200}
    err_data = {
        vars.RESPONSE: 400,
        vars.ERROR: 'Bad request'
    }

    def test_no_action(self):
        self.assertEqual(client_presence({
            vars.TIME: '0',
            vars.USER: {
                vars.ACCOUNT_NAME: 'Guest'
            }
        }), self.err_data)

    def test_no_time(self):
        self.assertEqual(client_presence({
            vars.ACTION: vars.PRESENCE,
            vars.USER: {
                vars.ACCOUNT_NAME: 'Guest'
            }
        }), self.err_data)

    def test_no_user(self):
        self.assertEqual(client_presence({
            vars.ACTION: vars.PRESENCE,
            vars.TIME: '0',
        }), self.err_data)

    def test_wrong_user(self):
        self.assertEqual(client_presence({
            vars.ACTION: vars.PRESENCE,
            vars.TIME: '0',
            vars.USER: {
                vars.ACCOUNT_NAME: 'Admin'
            }
        }), self.err_data)

    def test_ok(self):
        self.assertEqual(client_presence({
            vars.ACTION: vars.PRESENCE,
            vars.TIME: '0',
            vars.USER: {
                vars.ACCOUNT_NAME: 'Guest'
            }
        }), self.ok_data)


if __name__ == '__main__':
    unittest.main()
