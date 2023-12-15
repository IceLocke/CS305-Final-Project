import asyncio
import os
import request as req
import response as resp
import viewer


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
        path = request.path
        method = request.method
        handler = self.route_handler(path)

        response = resp.construct_response(handler())
        writer.write(response.encode('utf-8'))
        await writer.drain()
        writer.close()

    async def run_server(self, host, port):
        self.server = await asyncio.start_server()

    def run(self, host='localhost', port=8080):
        asyncio.run(self.run_server(host, port))
