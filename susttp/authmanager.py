import binascii

import susttp.request as req
import threading
import secrets
import base64


class AuthManager:
    def __init__(self):
        self.accounts = {}
        self.sessions = {}
        self.authenticated_func = []

    def get_username(self, session_id):
        if session_id in self.sessions.keys():
            return self.sessions[session_id]
        else:
            return None

    def filter(self, request: req.Request, handler):
        if handler.__name__ in self.authenticated_func:
            session_id = self.authorized(request)
            return session_id if session_id is not None else self.authenticate(request)
        else:
            return True

    def require_authentication(self):
        def warp(func):
            self.authenticated_func.append(func.__name__)
            return func
        return warp

    def authorized(self, request: req.Request):
        """
        Check whether a request is authorized
        :param request: the request objet
        :return: True if the request is authorized, otherwise False
        """
        # 检查是否已经认证过
        print(request.cookies)
        if request.cookies is not None:
            if "session-id" in request.cookies.keys():
                if request.cookies["session-id"] in self.sessions.keys():
                    return request.cookies['session-id']
        return None

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
            auth_info = auth_info.decode('ASCII').split(':')
            username, password = auth_info[0], auth_info[-1]
            if username in self.accounts.keys():
                if password == self.accounts[username]:
                    session_id = str(secrets.token_hex(32))
                    self.sessions[session_id] = username
                    threading.Timer(3600, lambda _session_id: self.sessions.pop(_session_id), session_id)
                    return session_id
        return None
