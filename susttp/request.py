import re


def parse(request):
    lines = request.split('\r\n')
    request_line = dict(zip(('Method', 'URL', 'Version'), lines[0].split()))
    headers = {}
    for line in lines[1:]:
        if line == '':
            break
        print(line)
        key, value = line.split(':', 1)
        headers[key] = value
    return request_line, headers


