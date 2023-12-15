test_req = 'HEAD url HTTP/1.1\r\nConnection:close\r\nContent-Length:114514\r\n\r\nbody'

def read(request):
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

headers = read(test_req)

print(headers)