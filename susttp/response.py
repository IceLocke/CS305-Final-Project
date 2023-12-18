import time


class Response:
    def __init__(self, http_version="HTTP/1.1", status=200, reason_phrase="OK",
                 header=None, body=None):
        self.http_version = http_version
        self.status = status
        self.reason_phrase = reason_phrase
        timestamp = time.time()
        time_struct = time.gmtime(timestamp)
        self.header = {
            'Server': 'ArchiveServer',
            'Date': time.strftime("%a, %d %b %H:%M:%S GMT", time_struct),
            'Content-Type': 'text/plain; charset=utf-8',
        } if header is None else header
        self.body = body.encode('utf-8') if body else None


    def build(self, chunked=False, chunk_size=4096):
        response = f'{self.http_version} {self.status} {self.reason_phrase}\r\n'
        for key in self.header:
            response += f'{key}: {self.header[key]}\r\n'
        response = response.encode('utf-8')
        if chunked:
            response += b'\r\n'
            current, next = 0, 0
            while current < len(self.body):
                next = min(current + chunk_size, len(self.body))
                response += str(next - current + 2).encode('utf-8') + b'\r\n'
                response += self.body[current: next] + b'\r\n'
                current = next
        else:
            if self.body:
                response += f'Content-Length: {len(self.body)}\r\n\r\n'.encode('utf-8')
                response += self.body
        print(response)
        return response


def unauthorized_response():
    return Response(status=401, reason_phrase='WWW-Authenticated: Basic realm=\"Authorization Required\"').build()


def forbidden_response():
    return Response(status=403, reason_phrase='Forbidden').build()


def not_find_response():
    return Response(status=404, reason_phrase='Not Found').build()


def method_not_allowed():
    return Response(status=405, reason_phrase='Method Not Allowed').build()


def html_response(html):
    res = Response(body=html)
    res.header['Content-Type'] = 'text/html'
    return res.build()


def download_response(body, chunked=False, chunk_size=4096):
    return Response(body=body).build(chunked=chunked, chunk_size=chunked)


def upload_response():
    return Response().build()
