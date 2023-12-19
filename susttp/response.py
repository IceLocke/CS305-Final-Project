import time


class Response:
    def __init__(self, http_version="HTTP/1.1", status=200, reason_phrase="OK",
                 header=None, body=None):
        self.http_version = http_version
        self.status = status
        self.reason_phrase = reason_phrase
        self.set_cookie = None
        timestamp = time.time()
        time_struct = time.gmtime(timestamp)
        self.header = {
                'Server': 'ArchiveServer',
                'Date': time.strftime("%a, %d %b %H:%M:%S GMT", time_struct),
                'Content-Type': 'text/plain; charset=utf-8',
            } if header is None else header
        self.body = body

    def add_cookie(self, key, value):
        if self.set_cookie is None:
            self.set_cookie = {}
        self.set_cookie[key] = value

    def build(self, chunked=False, chunk_size=4096):
        headers, body = f'{self.http_version} {self.status} {self.reason_phrase}\r\n', b''
        # Construct common headers
        for key, value in self.header.items():
            headers += f'{key}: {value}\r\n'
        # Construct cookies
        if self.set_cookie:
            set_cookie = '; '.join([f'{key}={value}' for (key, value) in self.set_cookie.items()])
            headers += f'Set-Cookie: {set_cookie}\r\n'

        if chunked:
            current_pos, next_pos = 0, 0
            while current_pos < len(self.body):
                next_pos = min(current_pos + chunk_size, len(self.body))
                body += str(next_pos - current_pos + 2).encode('utf-8') + b'\r\n'
                body += self.body[current_pos: next_pos] + b'\r\n'
                current_pos = next_pos
        else:
            body = self.body if self.body else b''
        headers += f'Content-Length: {len(body)}\r\n'
        return headers.encode('utf-8') + b'\r\n' + body


def unauthorized_response():
    return Response(status=401, reason_phrase='WWW-Authenticated: Basic realm=\"Authorization Required\"')


def forbidden_response():
    return Response(status=403, reason_phrase='Forbidden')


def not_find_response():
    return Response(status=404, reason_phrase='Not Found')


def method_not_allowed():
    return Response(status=405, reason_phrase='Method Not Allowed')


def html_response(html):
    res = Response(body=html.encode('utf-8'))
    res.header['Content-Type'] = 'text/html'
    return res


def file_download_response(file, content_type):
    res = Response(body=file)
    res.header['Content-Type'] = content_type
    res.header['Content-Disposition'] = 'attachment'
    return res


def upload_response():
    return Response()
