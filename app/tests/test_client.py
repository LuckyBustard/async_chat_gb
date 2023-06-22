import os
import sys
import unittest

sys.path.append(os.path.join(os.getcwd(), '..'))

from client import create_presence, process_answer
from common import vars


class TestServer(unittest.TestCase):

    def test_client_presence_ok(self):
        request = create_presence('Guest')
        request[vars.TIME] = '0'

        self.assertEqual(request, {
            vars.ACTION: vars.PRESENCE,
            vars.TIME: '0',
            vars.USER: {
                vars.ACCOUNT_NAME: 'Guest'
            }
        })

    def test_client_presence_fail(self):
        request = create_presence('Admin')
        request[vars.TIME] = '0'

        self.assertNotEqual(request, {
            vars.ACTION: vars.PRESENCE,
            vars.TIME: '0',
            vars.USER: {
                vars.ACCOUNT_NAME: 'Guest'
            }
        })

    def test_client_answer_ok(self):
        self.assertEqual(process_answer({vars.RESPONSE: 200}), '200: OK')

    def test_client_answer_fail(self):
        self.assertEqual(process_answer({vars.RESPONSE: 400, vars.ERROR: 'Some'}), '400: Some')

    def test_no_response(self):
        self.assertRaises(ValueError, process_answer, {})


if __name__ == '__main__':
    unittest.main()
