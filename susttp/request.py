class Request:
    def __init__(self, method, path, version, headers):
        self.method = method
        self.path = path
        self.version = version
        self.headers = headers
        self.request_param = None
        self.path_param = None
        self.anchor = None
        self.body = None


def parse(request):
    lines = request.split('\r\n')
    if len(lines[0].split()) != 3:
        return None
    request_line = dict(zip(('method', 'path', 'version'), lines[0].split()))

    headers = {}

    for line in lines[1:]:
        if line == '':
            break
        print(line)
        key, value = line.split(':', 1)
        headers[key] = value.strip()

    return Request(
        method=request_line['method'],
        path=request_line['path'],
        version=request_line['version'],
        headers=headers
    )


