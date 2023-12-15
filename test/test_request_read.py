import susttp.request

test_req = 'HEAD url HTTP/1.1\r\nConnection:close\r\nContent-Length:114514\r\n\r\nbody'

headers = susttp.request.parse(test_req)

print(headers)
