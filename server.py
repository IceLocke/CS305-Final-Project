import os.path
import toml

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
    os.chdir(root_dict)
    return file_system_template.render(head=path, files=files)


def error_html(status, reason):
    return error_template.render(head=f'{status} {reason}')


app = server.App()


@app.route("/<string:username>/<path>")
def file_view(request: req.Request):
    print(request.request_param, request.path_param)
    html = file_system_html(os.path.join(request.path_param['username'], request.path_param['path']))
    print(html)
    return resp.html_response(html)


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
