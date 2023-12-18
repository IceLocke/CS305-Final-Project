import os.path
import toml
import mimetypes

import susttp.app as server
import susttp.response as resp
import susttp.request as req

from jinja2 import Environment, PackageLoader, select_autoescape

# Jinja2 模板渲染
env = Environment(
    loader=PackageLoader("server"),
    autoescape=select_autoescape()
)
file_system_template = env.get_template("file_system.html")
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
    username = path.split('\\')[0].split('/')[0]
    files.append({'name': '/', 'path': '/' + username + '/'})
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


@app.route("/<string:username>/<path>", require_authentication=True)
def file_view(request: req.Request):
    username = request.path_param['username']
    path = os.path.join(request.path_param['username'], request.path_param['path'])
    # TODO: 检查是否有权限访问
    if is_server_dir(path):  # folder
        html = file_system_html(path)
        return resp.html_response(html)
    elif is_server_file(path):  # file
        file, content_type = file_binary(path)
        print(file)
        print(content_type)
        return resp.file_download_response(file=file, content_type=content_type)
    else:  # not found
        return resp.not_find_response()


@app.route("/upload")
def upload(request: req.Request):
    pass


@app.route("/delete")
def delete(request: req.Request):
    pass


@app.route("/chunk")
def delete(request: req.Request):
    pass


if __name__ == '__main__':
    app.run("localhost", 8081)
