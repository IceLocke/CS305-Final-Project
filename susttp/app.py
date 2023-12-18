import asyncio
import susttp.request as req
import susttp.response as resp
from functools import wraps
import threading
import re


class App:

    class DynamicRouteItem:
        @staticmethod
        def item_to_regex(item_type, item_name):
            type_to_regex = {
                'string': r'[^?/]*',
                'path': r'[^?]*',
            }
            if item_type not in type_to_regex.keys():
                item_type = 'path'
            return r'(?P<' + item_name + r'>' + type_to_regex[item_type] + r')'

        def __init__(self, path, func):
            self.route_target = func

            # 1. Calculate position of first wildcard
            self.first_wildcard_pos = path.split('<', 1)[0].count('/') if '<' in path else 100000

            # 2. Transform '<xxx>' part in the path into a regex
            self.names = []  # original names of wildcards
            pattern = r'\<[^<>?]*\>'  # extract <xxx> part
            matches = re.finditer(pattern, path)  # seems that this object cannot reverse
            delta_length = 0
            for match in matches:
                start = match.start() + delta_length
                end = match.end() + delta_length
                match_item = match.group()[1:-1]  # remove '<' and '>'
                if ':' in match_item:  # certain type
                    item_type, item_name = match_item.split(':', 1)
                else:
                    item_type, item_name = 'path', match_item  # in this project we set default to 'path'
                regex_form = self.item_to_regex(item_type, item_name)
                old_length = end - start
                new_length = len(regex_form)
                delta_length += new_length - old_length
                path = path[:start] + regex_form + path[end:]
                self.names.append(item_name)
            self.regex = path

    def __init__(self):
        self.dynamic_route_items = []  # List of DynamicRouteItem
        self.server = None

    def route(self, path):
        def warp(func):
            self.dynamic_route_items.append(self.DynamicRouteItem(path=path, func=func))
            return func
        return warp

    def route_handler(self, path):
        """
        :param path: path+parameters+anchor (str)
        :return:
            request_param: dict, request_param_name(str) -> request_param_value(str)
            path_param: dict, path_param_name(str) -> path_param_value(str)
            func: function, target callable function
            anchor: str, anchor
        """

        # 1. Split anchor
        anchor = ''
        if '#' in path:
            path, anchor = path.rsplit('#', 1)  # split from right side

        # 2. Split request params
        request_param = {}
        if '?' in path:
            path, request_str = path.rsplit('?', 1)  # split from right side
            # Split request_str into 'x=y' pairs
            request_param_items = request_str.split('&')
            for request_param_item in request_param_items:
                if '=' in request_param_item:
                    name, value = request_param_item.split('=', 1)
                else:
                    name, value = request_param_item, None
                request_param[name] = value

        # 3. Dynamic route
        max_match = -1
        max_match_route_item = None
        reg_match = None
        for dri in self.dynamic_route_items:
            regex = dri.regex
            match = re.match(regex, path)
            if match and dri.first_wildcard_pos > max_match:
                reg_match = match
                max_match_route_item = dri
                max_match = max_match_route_item.first_wildcard_pos
        path_param = {name: reg_match.group(name) for name in max_match_route_item.names} \
            if max_match_route_item is not None else {}
        func = max_match_route_item.route_target \
            if max_match_route_item is not None else None
        return request_param, path_param, func, anchor

    async def handle_client(self, reader, writer):
        request, line = "", None
        while line != '\r\n':
            line = (await reader.readline()).decode('utf8')
            request += line
            if line:
                print(line)
        print('finish input')
        request = req.parse(request)
        path, method = request.path, request.method
        request.request_param, request.path_param, handler, request.anchor = self.route_handler(path)
        if "Content-Length" in request.headers.keys():
            request.body = reader.read(request.headers["Content-Length"])
        if handler is None:
            response = resp.not_find_response()
        else:
            response = handler(request)
        writer.write(response.build())
        await writer.drain()
        writer.close()

    async def run_server(self, host, port):
        self.server = await asyncio.start_server(self.handle_client, host, port)
        async with self.server:
            await self.server.serve_forever()

    def run(self, host='localhost', port=8080):
        asyncio.run(self.run_server(host, port))

