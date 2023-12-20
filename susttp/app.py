import logging
import asyncio
import sys
import re

import susttp.request as req
import susttp.response as resp

from susttp.authmanager import AuthManager

STREAM_READER_BUFFER_LENGTH = 4096


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
        self.auth_manager = AuthManager()
        self.logger = logging.getLogger('SUSTTPServer')
        while self.logger.hasHandlers():
            self.logger.handlers.pop()
        self.logger.addHandler(logging.StreamHandler(sys.stdout))

    def route(self, path, require_authentication=False):
        def warp(func):
            self.dynamic_route_items.append(self.DynamicRouteItem(path=path, func=func))
            if require_authentication:
                self.auth_manager.require_authentication(func.__name__)
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

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.logger.info('New client connected')
        request = None
        try:
            request = (await reader.readuntil(b'\r\n\r\n')).decode('utf-8')
        except asyncio.IncompleteReadError as e:
            print(e)
        if request and len(request) < 1024:
            self.logger.info(f'Get request:\n{request}')
        else:
            self.logger.info('Get request: [too long]')
        if request:
            # get route
            request = req.parse(request)
            path, method = request.path, request.method
            request.request_param, request.path_param, handler, request.anchor = self.route_handler(path)

            # read body
            if "Content-Length" in request.headers.keys():
                total_length = int(request.headers["Content-Length"])
                if total_length:
                    buffer_length = STREAM_READER_BUFFER_LENGTH
                    if total_length <= buffer_length:
                        request.body = await reader.read()
                    else:
                        request.body = b''
                        while len(request.body) < total_length:
                            request.body = request.body + await reader.read(
                                max(buffer_length, total_length - len(request.body))
                            )
            if handler is None:
                self.logger.info(f'Cannot find resource {request.path}')
                response = resp.not_found_response()
            else:
                # True / session-id will pass the filter
                self.logger.info('Applying security filter')
                filter_result = self.auth_manager.filter(request, handler)
                if filter_result is True:
                    self.logger.info(f'Passed filter, route to handler {handler.__name__}')
                    # handle
                    response = handler(request)
                elif filter_result.__class__ is str:
                    self.logger.info(f'Authenticated with session-id: {filter_result}')
                    response = resp.Response()
                    response.add_cookie('session-id', filter_result)
                    response.add_cookie('Path', '/')
                else:
                    self.logger.info('Cannot pass filter, route to authentication entry point')
                    response = self.auth_manager.entry_func(request)
        else:
            response = resp.Response(status=400, reason_phrase='Bad Request')

        # response
        res = response.build()
        writer.write(res)
        if res and len(res) < 1024:
            self.logger.info(f'Response: {res}')
        else:
            self.logger.info('Response: [too long]')
        await writer.drain()
        writer.close()

    async def run_server(self, host, port):
        self.server = await asyncio.start_server(self.handle_client, host, port)
        async with self.server:
            await self.server.serve_forever()

    def run(self, host='localhost', port=8080, debug=True):
        if debug:
            self.logger.setLevel(logging.INFO)
        self.logger.info(f'SUSTech HTTP server now runs on {host}:{port}')
        asyncio.run(self.run_server(host, port))

