import susttp.server as sttp
import os

import susttp.response as resp
import susttp.request as req

app = sttp.App()

app.run("localhost", 8080)


# localhost:8080/123456/abc/abc
@app.route("/<username>/<path>")
def get_file(request: req.Request, body):
    username = request.path_param['username']
    path = request.path_param['path']





