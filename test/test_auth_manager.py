import unittest
import susttp.authmanager as auth_manager
import susttp.request as req


class MyTestCase(unittest.TestCase):
    def test_filter(self):

        manager = auth_manager.AuthManager()
        manager.accounts = {
            "usr0": "pwd0",
            "usr1": "pwd1"
        }

        @manager.require_authentication()
        def test_func():
            pass

        request_no_auth = req.parse(
            "GET / HTTP/1.1"
        )
        request_need_auth = req.parse(
            "GET / HTTP/1.1"
        )



if __name__ == '__main__':
    unittest.main()
