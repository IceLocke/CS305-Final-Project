class Response:
    def __init__(self, http_version="HTTP/1.1", status=200, reason_phrase="OK",
                 header=None, body=None):
        self.http_version = http_version
        self.status = status
        self.reason_phrase = reason_phrase
        self.header = {} if header is None else header
        self.body = body

    def build(self):
        response = ""
        response.join(f'{self.http_version} {self.status} {self.reason_phrase}\r\n')
        for key, value in self.header:
            response.join(f'{key}:{value}\r\n')
        response = response.encode('utf-8')
        if self.body is not None:
            response.join(bytes(self.body))
        return response
