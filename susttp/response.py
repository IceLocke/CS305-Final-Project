import time


class Response:
    def __init__(self, http_version="HTTP/1.1", status=200, reason_phrase="OK",
                 headers=None, content_type='text/plain; charset=utf-8', body=None,
                 chunked=False, chunk_size=4096, ranges=None):
        self.http_version = http_version
        self.status = status
        self.reason_phrase = reason_phrase
        self.set_cookie = {}
        self.chunked = chunked
        self.chunk_size = chunk_size
        self.ranges = ranges
        timestamp = time.time()
        time_struct = time.gmtime(timestamp)
        self.headers = {
            'Server': 'SUSTTP Server',
            'Date': time.strftime("%a, %d %b %H:%M:%S GMT", time_struct),
            'Content-Type': content_type,
        } if headers is None else headers
        self.body = body
        self.process()

    def add_cookie(self, key, value):
        self.set_cookie[key] = value

    def process(self):
        # Process headers and body
        body = None

        # Range
        if self.ranges is not None:
            if len(self.ranges) == 1:
                l, r = self.ranges[0]
                self.headers['Content-Range'] = f'bytes {l}-{r}/{len(self.body)}'
                body = self.body[l: r + 1]
            else:
                content_type = self.headers['Content-Type']
                self.headers['Content-Type'] = 'multipart/byteranges; boundary=3d6b6a416f9b5'
                body = b''
                for l, r in self.ranges:
                    body += b'--3d6b6a416f9b5\r\n'
                    body += f'Content-Type: {content_type}\r\n'.encode('utf-8')
                    body += f'Content-Range: bytes {l}-{r}/{len(self.body)}\r\n'.encode('utf-8')
                    body += b'\r\n'
                    body += self.body[l: r + 1]
                    body += b'\r\n'
                body += b'--3d6b6a416f9b5--'

            self.headers['Content-Length'] = str(len(body))

        # Chunk
        elif self.chunked:
            self.headers['Transfer-Encoding'] = 'chunked'
            current_pos, next_pos = 0, 0
            body = b''
            while current_pos < len(self.body):
                next_pos = min(current_pos + self.chunk_size, len(self.body))
                body += str(hex(next_pos - current_pos))[2:].encode('utf-8') + b'\r\n'  # 十六进制去掉0x
                body += self.body[current_pos: next_pos] + b'\r\n'
                current_pos = next_pos
            body += b'0\r\n\r\n'

        # Plain body
        elif self.body:
            body = self.body
            self.headers['Content-Length'] = str(len(body))

        self.body = body

    def build(self):
        # Construct status line
        response = f'{self.http_version} {self.status} {self.reason_phrase}\r\n'

        # Construct headers
        for key, value in self.headers.items():
            response += f'{key}: {value}\r\n'

        # Cookie
        if self.set_cookie != {}:
            response += 'Set-Cookie: '
            response += '; '.join([f'{key}={value}' for (key, value) in self.set_cookie.items()])
            response += '\r\n'

        response += '\r\n'
        response = response.encode('utf-8')

        # Construct body
        if self.body is not None:
            response += self.body

        return response

    def set_to_head(self, method_is_head: bool):
        """
        If method is HEAD, set body to None
        :param method_is_head: if method is HEAD
        :return: self
        """
        if method_is_head:
            self.body = None
        return self


def bad_request_response():
    return Response(status=400, reason_phrase='Bad Request')


def unauthorized_response():
    return Response(status=401, reason_phrase='WWW-Authenticated: Basic realm=\"Authorization Required\"')


def forbidden_response():
    return Response(status=403, reason_phrase='Forbidden')


def not_found_response():
    return Response(status=404, reason_phrase='Not Found')


def method_not_allowed():
    return Response(status=405, reason_phrase='Method Not Allowed')


def html_response(html):
    res = Response(content_type='text/html', body=html.encode('utf-8'))
    return res


def range_not_satisfiable():
    return Response(status=416, reason_phrase='Range Not Satisfiable')


def file_download_response(file, content_type, chunked=False, ranges=None):
    if ranges is not None:
        res = Response(status=206, reason_phrase='Partial Content',
                       content_type=content_type, body=file, ranges=ranges)
    else:
        res = Response(content_type=content_type, body=file, chunked=chunked)
    res.headers['Content-Disposition'] = 'attachment'
    return res


def text_response(text):
    return Response(body=text.encode('utf-8'))
