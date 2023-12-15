import os
import time
from yattag import Doc
from susttp.server import App

def directory_viewer(path):
    doc, tag, text = Doc().tagtext()
    with tag('html'):
        with tag('body'):
            with tag('table'):
                with tag('tr'):
                    with tag('th'):
                        text('Name')
                    with tag('th'):
                        text('Size')
                    with tag('th'):
                        text('Last Modified')
                for file_name in os.listdir(path):
                    file_path = os.path.join(path, file_name)
                    with tag('tr'):
                        with tag('td'):
                            with tag('a', href=file_path):
                                text(file_name)
                        with tag('td'):
                            text(f'{os.path.getsize(file_path) / 1024 : .2f} KB')
                        with tag('td'):
                            stamp = time.localtime(os.path.getmtime(file_path))
                            text(f'{stamp.tm_year}/{stamp.tm_mon}/{stamp.tm_mday} {stamp.tm_hour}:{stamp.tm_min}')
    return doc.getvalue()


app = App()


@app.route('/<username>/<path>')
def op(request):
    username = request.path_param['username']
    path = request.path_param["path"]
    method = request.method
    dir_path = os.path.join(os.getcwd(), 'data', username, path)
    return ops[method](dir_path)


def get(path):
    if os.path.exists(path):
        return BADREQUES
    content = None
    with open(path) as file:
        content = file.read()
    return OK(content)


def head(path):
    if os.path.exists(path):
        return BADREQUES
    return OK(None)


def post(path):
    pass


ops = {
    'GET': get,
    'HEAD': head,
    'POST': post,
}


if __name__ == '__main__':
    app.run()
    