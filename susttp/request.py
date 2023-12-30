class Request:
    def __init__(self, method, path, version, headers, cookies=None):
        self.method = method
        self.path = path
        self.version = version
        self.headers = headers
        self.request_param = None
        self.path_param = None
        self.cookies = cookies
        self.anchor = None
        self.body = None

    def add_cookie(self, name, value):
        """
        kl: 用于登录后强行插入一条session-id进入request的cookie，模拟成重新发来的指令
        是一个介于测试脚本和我们原本设计之间的adapter
        :param name: cookie name
        :param value: cookie value
        :return: nothing
        """
        if self.cookies is None:
            self.cookies = {}
        self.cookies[name] = value


def parse(request):
    lines = request.split('\r\n')
    if len(lines[0].split()) != 3:
        return None
    request_line = dict(zip(('method', 'path', 'version'), lines[0].split()))

    headers = {}

    for line in lines[1:]:
        if line == '':
            break
        key, value = line.split(':', 1)
        headers[key] = value.strip()

    cookies = None
    if "Cookie" in headers.keys():
        cookies = {}
        for cookie in headers["Cookie"].split(";"):
            key, value = cookie.split("=", 1)
            cookies[key.strip()] = value

    return Request(
        method=request_line['method'],
        path=request_line['path'],
        version=request_line['version'],
        headers=headers,
        cookies=cookies,
    )

