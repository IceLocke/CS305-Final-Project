import binascii
import time

import susttp.request as req
import susttp.response as resp
import secrets
import base64


class AuthManager:
    def __init__(self, expire_time=3600):
        self.accounts = {
            '10000000': 'pwd0',
            '10000001': 'pwd1'
        }
        self.sessions = {}
        self.username_map = {}
        self.authenticated_func = []
        self.entry_func = lambda _: resp.unauthorized_response()
        self.expire_time = expire_time

    def get_username(self, session_id):
        if session_id in self.sessions.keys():
            return self.sessions[session_id]['username']
        else:
            return None

    def get_session_id(self, username):
        if username in self.username_map.keys():
            return self.username_map[username]

    def filter(self, request: req.Request, handler):
        if handler.__name__ in self.authenticated_func:
            authorized = self.authorized(request)
            if authorized:
                print("authorized")
            return True if authorized else self.authenticate(request)
        else:
            return True

    def entry_point(self):
        def warp(func):
            self.entry_func = func
            return func
        return warp

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
                        # self.username_map.pop(self.sessions[session_id]['username'])
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
                self.sessions[session_id] = {'username': username, 'expire_time': time.time() + self.expire_time}
                if username in self.username_map.keys():
                    self.sessions.pop(self.username_map[username])
                self.username_map[username] = session_id
                return session_id
        return None
