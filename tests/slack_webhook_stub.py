"""Stand-in for a Slack incoming webhook, for a GitHub Actions step.

Writes the body of every POST to the file given as argument, and the URL to
post to as the step's `url` output. Returns once listening and serves from a
background process, so the next step can post to it right away.
"""

import http.server
import os
import pathlib
import sys

payload_path = pathlib.Path(sys.argv[1])


class Handler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        payload_path.write_bytes(self.rfile.read(int(self.headers["Content-Length"])))
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")


server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
with open(os.environ["GITHUB_OUTPUT"], "a") as output:
    output.write(f"url=http://127.0.0.1:{server.server_port}/\n")
if os.fork() == 0:
    # Off the step's output: it ends with the step, and the runner may wait
    # for whoever still holds it.
    devnull = os.open(os.devnull, os.O_RDWR)
    for fd in (0, 1, 2):
        os.dup2(devnull, fd)
    server.serve_forever()
