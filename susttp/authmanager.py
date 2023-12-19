import binascii
import time

import susttp.request as req
import secrets
import base64


class AuthManager:
    def __init__(self):
        self.accounts = {
            '10000000': 'pwd0',
            '10000001': 'pwd1'
        }
        self.sessions = {}
        self.authenticated_func = []

    def get_username(self, session_id):
        if session_id in self.sessions.keys():
            return self.sessions[session_id]['username']
        else:
            return None

    def filter(self, request: req.Request, handler):
        if handler.__name__ in self.authenticated_func:
            authorized = self.authorized(request)
            return True if authorized else self.authenticate(request)
        else:
            return True

    def require_authentication(self, name):
        self.authenticated_func.append(name)

    def authorized(self, request: req.Request):
        """
        Check whether a request is authorized
        :param request: the request objet
        :return: True if the request is authorized, otherwise False
        """
        # 检查是否已经认证过
        if request.cookies is not None:
            if "session-id" in request.cookies.keys():
                session_id = request.cookies["session-id"]
                if session_id in self.sessions.keys():
                    if time.time() < self.sessions[session_id]['expire_time']:
                        return True
                    else:
                        self.sessions.pop(session_id)
                        return False
        return False

    def authenticate(self, request: req.Request):
        """
        Do authentication
        :param request: the request object
        :return: `session-id` if the request is authenticated, otherwise `None`
        """
        headers = request.headers
        # 否则检查是否试图认证
        if 'Authorization' in headers.keys():
            auth_info = headers['Authorization'].split()[-1]
            try:
                auth_info = base64.b64decode(bytes(auth_info, 'ASCII'))
            except binascii.Error as e:
                print(e)
                return None
            auth_info = auth_info.decode('ASCII').split(':')
            username, password = auth_info[0], auth_info[-1]
            if (username, password) in self.accounts.items():
                session_id = str(secrets.token_hex(32))
                self.sessions[session_id] = {'username': username, 'expire_time': time.time() + 3600}
                return session_id
        return None
