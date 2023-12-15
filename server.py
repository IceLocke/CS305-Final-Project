import os.path
import toml
import base64
import secrets

import susttp.server as server
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
error_template = env.get_template("error.html")


def check_authorization(request: req.Request):
    """
    Check whether a request is authorized
    :param request: the request objet
    :return: `session-id` if the request is authorized, otherwise `None`
    """
    headers = request.headers
    # 检查是否已经认证过
    if "Cookie" in headers.keys():
        cookies = {}
        for cookie in headers["Cookie"].split(";"):
            key, value = cookie.split("=", 1)
            cookies[key.strip()] = value
        if "session-id" in cookies.keys():
            if cookies["session-id"] in sessions.keys():
                return cookies["session-id"]
    return None


def authenticate(request: req.Request):
    """
    Do authentication
    :param request: the request object
    :return: `session-id` if the request is authenticated, otherwise `None`
    """
    headers = request.headers
    # 否则检查是否试图认证
    if 'Authorization' in headers.keys():
        auth_info = headers['Authorization'].split()[-1]
        auth_info = base64.b64decode(auth_info).split(':')
        username, password = auth_info[0], auth_info[-1]
        if username in accounts.keys():
            if password == accounts[username]:
                session_id = str(secrets.token_hex(32))
                sessions[session_id] = username
                return session_id
    return None


def file_system_html(path):
    root_dict, files = os.getcwd(), []
    view_path = os.path.join(root_dict, 'data', path)
    print(view_path)
    os.chdir(view_path)
    files.append({'name': '/', 'path': '/'+path.split('/')[0]+'/'})
    files.append({'name': '../', 'path': '../'})
    for file in os.listdir('.'):
        if os.path.isdir(file):
            file += '/'
        files.append({
            'name': file,
            'path': '/' + str(os.path.join(path, file))
        })
    return file_system_template.render(head=path, files=files)


def error_html(status, reason):
    return error_template.render(head=f'{status} {reason}')


app = server.App()


@app.route("/<username>/<path>")
def file_view(request: req.Request, body):
    username = request.path_param['username']
    path = request.path_param['path']


@app.route("/upload")
def upload(request: req.Request, body):
    pass


@app.route("/delete")
def delete(request: req.Request, body):
    pass


@app.route("/chunk")
def delete(request: req.Request, body):
    pass


if __name__ == '__main__':
    app.run("localhost", 8080)
