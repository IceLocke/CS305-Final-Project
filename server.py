import os.path
import toml
import mimetypes
import argparse

import shutil  # delete dir
import susttp.app as server
import susttp.response as resp
import susttp.request as req

from jinja2 import Environment, PackageLoader, select_autoescape

# 认证相关
accounts = {}
sessions = {}
config = toml.load("config.toml")
for account in config["accounts"]:
    accounts[config["accounts"][account]["username"]] = config["accounts"][account]["password"]

# Jinja2 模板渲染
env = Environment(
    loader=PackageLoader("server"),
    autoescape=select_autoescape()
)
file_system_template = env.get_template("file_system.html")
login_template = env.get_template("login.html")
error_template = env.get_template("error.html")


def is_server_file(path):
    root_dict = os.getcwd()
    target_path = os.path.join(root_dict, 'data', path)
    return os.path.isfile(target_path)


def is_server_dir(path):
    root_dict = os.getcwd()
    target_path = os.path.join(root_dict, 'data', path)
    return os.path.isdir(target_path)


def is_server_path(path):
    root_dict = os.getcwd()
    target_path = os.path.join(root_dict, 'data', path)
    return os.path.exists(target_path)


def file_system_html(path):
    root_dict, files = os.getcwd(), []
    view_path = os.path.join(root_dict, 'data', path)
    os.chdir(view_path)
    files.append({'name': '/', 'path': '/', 'delete': False})
    files.append({'name': '../', 'path': '../', 'delete': False})
    for file in os.listdir('.'):
        if os.path.isdir(file):
            file = os.path.join(file, '')
        files.append({
            'name': file,
            'path': '/' + os.path.join(path, file).replace('\\', '/'),
            'delete': True
        })
    os.chdir(root_dict)
    return file_system_template.render(head=path, files=files)


def file_system_list(path):
    root_dict, files = os.getcwd(), []
    view_path = os.path.join(root_dict, 'data', path)
    os.chdir(view_path)
    for file in os.listdir('.'):
        if os.path.isdir(file):
            file = file + '/'
        files.append(str(file))
    os.chdir(root_dict)
    # return str like '["A.txt", "B.exe", "C/"]'
    return '[' + ', '.join(['"' + file + '"' for file in files]) + ']'


def file_binary(path):
    root_dict = os.getcwd()
    file_path = os.path.join(root_dict, 'data', path)
    content_type, _ = mimetypes.guess_type(file_path)
    with open(file_path, 'rb') as file:
        binary_data = file.read()
    return binary_data, content_type


def error_html(status, reason):
    return error_template.render(head=f'{status} {reason}')


def resolve_form_data(data: bytes, boundary: bytes):
    """
    :param data: request body
    :param boundary: in request headers
    :return: list of (file: bytes, filename: str) pairs
    """
    filelist = []
    for data_part in data.split(b'--' + boundary):
        if data_part == b'':
            continue
        if b'\r\n\r\n' not in data_part:  # last part = boundary + '--\r\n'
            break
        data_part = data_part.split(b'\r\n\r\n')
        header, body = data_part[0], data_part[-1]
        lines = header.split(b'\r\n')
        header_dict = {}  # if needed, this contains 'Content-Type'
        disposition_dict = {}
        for line in lines:
            if line == b'':
                continue
            line = line.split(b':')
            name, value = line[0], line[-1]
            name = name.strip()
            value = value.strip()
            if name == b'Content-Disposition':
                key_value_pairs = value.split(b';')
                for key_value_pair in key_value_pairs:
                    key_value_pair = key_value_pair.split(b'=')
                    key, value = key_value_pair[0], key_value_pair[-1]
                    key = key.strip()
                    value = value.strip().strip(b'"')
                    disposition_dict[key] = value
            else:
                header_dict[name] = value
        filename = disposition_dict[b'filename'].decode()
        file = body[:-2]  # remove last '\r\n'
        filelist.append((file, filename))
    return filelist


def file_system_upload(path: str, file: bytes, filename: str):
    root_dict = os.getcwd()
    view_path = os.path.join(root_dict, 'data', path)
    os.chdir(view_path)
    with open(filename, 'wb') as f:
        f.write(file)
    os.chdir(root_dict)


def file_system_delete(path: str):
    root_dict = os.getcwd()
    path = os.path.join(root_dict, 'data', path)
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        elif os.path.isfile(path):
            os.remove(path)
        else:
            return True
    except OSError as e:
        print(e)
        return True
    return False


app = server.App()


@app.route("/<path>", require_authentication=True)
def file_view(request: req.Request):
    if request.method != 'GET':
        return resp.method_not_allowed()
    path = request.path_param['path']
    if is_server_file(path):  # file
        file, content_type = file_binary(path)
        chunked = ('chunked', '1') in request.request_param.items()
        if 'Range' in request.headers:
            range_list = request.headers['Range'].split(',')
            ranges = []
            for byte_range in range_list:
                if byte_range.startswith('-'):
                    l, r = len(file) - int(byte_range[1:]) + 1, len(file)
                elif byte_range.endswith('-'):
                    l, r = int(byte_range[:-1]), len(file)
                else:
                    l, r = map(int, byte_range.split('-'))
                if r < l or l > len(file) or r > len(file):
                    return resp.range_not_satisfiable()
                ranges.append((l, r))
            return resp.file_download_response(file=file, content_type=content_type, ranges=ranges)
        else:
            return resp.file_download_response(file=file, content_type=content_type, chunked=chunked)
    elif is_server_dir(path):  # folder
        if ('SUSTech-HTTP', '1') in request.request_param.items():
            file_list = file_system_list(path)  # return value is str
            return resp.text_response(file_list)
        else:
            html = file_system_html(path)
            return resp.html_response(html)
    else:  # not found
        return resp.not_found_response()


def post_request_permission_test(request: req.Request):
    # 1. wrong method
    if request.method != 'POST':
        return resp.method_not_allowed()

    # 2. no path provided
    if 'path' not in request.request_param.keys():
        return resp.bad_request_response()

    # 3. permission test
    path = str(request.request_param['path'])
    if path.startswith('/'):
        path = path[1:]  # remove the first '/'
    path_username = path.split('/')[0]
    """
        path = xxx or path = /xxx or path = xxx/ -> path_username = xxx
        path = empty -> path_username = empty
        path = //xxx -> path_username = empty  [is this correct?]
    """
    session_username = str(app.auth_manager.get_username(request.cookies['session-id']))
    if path_username != session_username:
        return resp.forbidden_response()

    return None  # Passed test


@app.route("/upload", require_authentication=True)
def upload(request: req.Request):
    result = post_request_permission_test(request=request)
    if result is not None:
        return result

    path = str(request.request_param['path'])
    if path.startswith('/'):
        path = path[1:]  # remove the first '/'

    # 4. server not found
    if not is_server_dir(path):
        return resp.not_found_response()

    # Upload file
    file, filename = resolve_form_data(
        data=request.body,
        boundary=(request.headers['Content-Type'].split('boundary=')[1]).encode('utf-8')
    )[0]
    file_system_upload(path, file, filename)
    return resp.Response()


@app.route("/delete", require_authentication=True)
def delete(request: req.Request):
    result = post_request_permission_test(request=request)
    if result is not None:
        return result

    path = str(request.request_param['path'])
    if path.startswith('/'):
        path = path[1:]  # remove the first '/'

    # 4. server not found
    if not is_server_path(path):
        return resp.not_found_response()

    # Delete file
    if file_system_delete(path):
        # System error. Shall we handle?
        return resp.Response()
    return resp.Response()


@app.auth_manager.entry_point()
def authenticate(request: req.Request):
    response = resp.unauthorized_response()
    response.body = login_template.render().encode('utf-8')
    response.headers['Content-Type'] = 'text/html'
    return response


parser = argparse.ArgumentParser()
parser.add_argument('-i', default='localhost')
parser.add_argument('-p', default='8080')
args = parser.parse_args()
if __name__ == '__main__':
    ip = args.i
    port = args.p
    app.run(ip, port)
