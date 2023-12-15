import asyncio
import request as req
import response as resp


class App:

    def __init__(self):
        self.url_map = {}
        self.server = None

    def route(self, path):
        def warp(func):
            self.url_map[path] = func
            return func

        return warp

    def route_handler(self, path):
        request_param, path_param, func = None, None, None
        return request_param, path_param, func

    async def handle_client(self, reader, writer):
        request, line = "", None
        while line != '\r\n':
            line = (await reader.readline()).decode('utf8')
            request += line
        request = req.parse(request)
        path, method = request.path, request.method
        req_param, path_param, handler = self.route_handler(path)

        response = handler(req_param, path_param)
        writer.write(response.encode('utf-8'))
        await writer.drain()
        writer.close()

    async def run_server(self, host, port):
        self.server = await asyncio.start_server()

    def run(self, host='localhost', port=8080):
        asyncio.run(self.run_server(host, port))
