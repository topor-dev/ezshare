import os
import re
import sys
from functools import partial
from http import server
from http.server import HTTPStatus
from io import BytesIO


class MethodDisabler:
    def empty_method(*args, **kwargs):
        pass

    def __init__(self, owner, method):
        self.owner = owner
        self.method = method

    def disable(self):
        if not hasattr(self, '_disabled'):
            self._disabled = False
        if self._disabled:
            return
        self._disabled = True
        self.orig = getattr(self.owner, self.method)
        setattr(self.owner, self.method, MethodDisabler.empty_method)

    def enable(self):
        if not self._disabled:
            return
        self._disabled = False
        setattr(self.owner, self.method, self.orig)

    def __enter__(self):
        self.disable()
        return self

    def __exit__(self, a, b, c):
        self.enable()


class Const:
    upload_url = '/_upload'
    html_uplod_link = '<a href="{url}"">upload file</a>'
    html_upload_form = '''\
<!DOCTYPE html><html>
<title>Upload file</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<body>
    <form action="{url}"" method="post" enctype="multipart/form-data">
        <input type="file" name="file"/>
        <input type="submit" value="send"/>
    <form>
</body>
</html>'''


def _send_upload_form_head(handler):
    self = handler
    enc = sys.getfilesystemencoding()
    self.send_response(HTTPStatus.OK)
    self.send_header('Content-type', 'text/html; charset=%s' % enc)
    encoded = Const.html_upload_form.format(url=Const.upload_url).encode(
        enc, errors='surrogatepass'
    )
    self.send_header('Content-Length', str(len(encoded)))
    self.end_headers()
    return BytesIO(encoded)


def send_head_and_inject_upload_link(handler):
    self = handler
    f = None
    with MethodDisabler(server.SimpleHTTPRequestHandler, 'end_headers'):
        f = self.send_head()
        if not f:
            return f
        enc = sys.getfilesystemencoding()
        before, after = f.read().decode(enc, errors='surrogatepass').split('<body>', 1)
        encoded = ''.join(
            [
                before,
                '<body>',
                Const.html_uplod_link.format(url=Const.upload_url),
                after,
            ]
        ).encode(enc, errors='surrogatepass')

        for i, val in enumerate(self._headers_buffer):
            if b'Content-Length' in val:
                del self._headers_buffer[i]
        self.send_header('Content-Length', str(len(encoded)))
        f.seek(0)
        f.write(encoded)
        f.seek(0)
    self.end_headers()
    return f


class ShareAndUploadHTTPRequestHandler(server.SimpleHTTPRequestHandler):
    def __init__(self, *args, directory=None, **kwargs):
        if directory is None:
            raise ValueError(directory)
        super().__init__(*args, directory=directory, **kwargs)

    def do_HEAD(self):
        f = self._send_head_with_inject()
        if f:
            f.close()

    def do_GET(self):
        f = self._send_head_with_inject()
        if f:
            try:
                self.copyfile(f, self.wfile)
            finally:
                f.close()

    def _send_head_with_inject(self):
        f = None
        if self.path == Const.upload_url:
            f = _send_upload_form_head(self)
        else:
            if not os.path.isdir(self.translate_path(self.path)):
                return super().do_GET()
            # else - directory - have to inject link
            f = send_head_and_inject_upload_link(self)
        return f

    def _fail(self):
        self.send_response(HTTPStatus.BAD_REQUEST)
        self.end_headers()
        return False

    def do_POST(self):  # upload file
        is_success = self.process_file_upload()
        if not is_success:
            return
        self.send_response(HTTPStatus.SEE_OTHER)
        self.send_header('Location', '/')
        self.end_headers()

    def process_file_upload(self):
        content_type = self.headers['content-type']
        if not content_type:
            return self._fail()
        if not '=' in content_type:
            return self._fail()
        boundary = content_type.split('=')[1].encode()
        remainbytes = int(self.headers['content-length'])
        line = self.rfile.readline()
        remainbytes -= len(line)
        if not boundary in line:
            return self._fail()
        line = self.rfile.readline()
        remainbytes -= len(line)
        fn = re.findall(
            r'Content-Disposition.*name="file"; filename="(.*)"', line.decode()
        )
        if not fn:
            return self._fail()
        file_name = fn[0]
        file_path = self.next_non_existing_file_path(file_name)

        # two empty lines
        remainbytes -= len(self.rfile.readline())
        remainbytes -= len(self.rfile.readline())
        with open(file_path, 'wb') as file:
            prevline = self.rfile.readline()
            remainbytes -= len(prevline)
            while remainbytes > 0:
                line = self.rfile.readline()
                remainbytes -= len(line)
                if boundary in line:
                    prevline = prevline[:-1]
                    if prevline.endswith(b'\r'):
                        prevline = prevline[:-1]
                    file.write(prevline)
                    return True
                else:
                    file.write(prevline)
                    prevline = line
        return self._fail()

    def next_non_existing_file_path(self, file_name):
        fname = os.path.join(self.directory, file_name)
        if not os.path.exists(fname):
            return fname
        counter = 1
        fname += '.'
        while os.path.exists(fname + str(counter)):
            counter += 1
        return fname + str(counter)


class UploadOnlyHttpRequestHandler(ShareAndUploadHTTPRequestHandler):
    def do_HEAD(self):
        f = _send_upload_form_head(self)
        if f:
            f.close()

    def do_GET(self):
        f = _send_upload_form_head(self)
        if f:
            try:
                self.copyfile(f, self.wfile)
            finally:
                f.close()


def serve(share_only, upload_only, port, directory):
    handler = None
    if share_only:
        handler = partial(server.SimpleHTTPRequestHandler, directory=str(directory))
    elif upload_only:
        handler = partial(UploadOnlyHttpRequestHandler, directory=str(directory))
    else:
        handler = partial(ShareAndUploadHTTPRequestHandler, directory=str(directory))

    server_address = ('', port)

    with server.ThreadingHTTPServer(server_address, handler) as httpd:
        httpd.serve_forever()
