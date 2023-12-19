import os.path
import toml
import mimetypes
import argparse

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


def file_system_html(path):
    root_dict, files = os.getcwd(), []
    view_path = os.path.join(root_dict, 'data', path)
    os.chdir(view_path)
    files.append({'name': '/', 'path': '/'})
    files.append({'name': '../', 'path': '../'})
    for file in os.listdir('.'):
        if os.path.isdir(file):
            file = os.path.join(file, '')
        files.append({
            'name': file,
            'path': '/' + os.path.join(path, file)
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
            range_list = request.headers['Range'][6:].split(',') # remove starting 'bytes='
            range = []
            for byte_range in range_list:
                if byte_range.startswith('-'):
                    l, r = len(file) - int(byte_range[1:]) + 1, len(file)
                elif byte_range.endswith('-'):
                    l, r = int(byte_range[:-1]), len(file)
                else:
                    l, r = map(int, byte_range.split('-'))
                if r < l or l > len(file) or r > len(file):
                    return resp.range_not_satisfiable()
                range.append((l, r))
            return resp.file_download_response(file=file, content_type=content_type, range=range)
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
        return resp.not_find_response()


@app.route("/upload", require_authentication=True)
def upload(request: req.Request):
    if request.method != 'POST':
        return resp.method_not_allowed()
    pass


@app.route("/delete", require_authentication=True)
def delete(request: req.Request):
    if request.method != 'POST':
        return resp.method_not_allowed()
    pass


@app.route("/chunk")
def delete(request: req.Request):
    pass


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

