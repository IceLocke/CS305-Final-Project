import unittest
import susttp.authmanager as auth_manager
import susttp.request as req


class MyTestCase(unittest.TestCase):
    def test_filter(self):
        manager = auth_manager.AuthManager()
        manager.accounts = {
            "10000000": "pwd0",
            "10000001": "pwd1"
        }

        @manager.require_authentication()
        def test_func():
            pass

        request_no_auth = req.parse(
            "GET / HTTP/1.1\r\n\r\n"
        )
        request_need_auth = req.parse(
            "GET / HTTP/1.1\r\n" + \
            "Authorization: Basic dXNyMDpwd2Qx\r\n\r\n"
        )

        result_1 = manager.filter(request_no_auth, test_func)
        print(f'result 1: {result_1}')

        result_2 = manager.filter(request_need_auth, test_func)
        print(f'result 2: {result_2}')

        request_has_auth = req.parse(
            "GET / HTTP/1.1r\r\n" + \
            f"Cookie: session-id={result_2}; test-value=1\r\n\r\n"
        )
        result_3 = manager.filter(request_has_auth, test_func)
        print(f'result_3: {result_3}')


if __name__ == '__main__':
    unittest.main()
