from threading import Thread

from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import pathlib
import mimetypes

import socket
from concurrent import futures as cf

import json

TCP_IP = 'localhost'
TCP_PORT = 5000

HTTP_PORT = 3000


class HTTPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        print(self.path)
        pr_url = urllib.parse.urlparse(self.path)
        print(pr_url)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message':
            self.send_html_file('message.html')
        elif pr_url.path == '/contact':
            self.send_html_file('contact.html')
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)

    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        print(data)
        data_parse = urllib.parse.unquote_plus(data.decode())
        print(data_parse)
        data_dict = {key: value for key, value in [
            el.split('=') for el in data_parse.split('&')]}
        print(data_dict)
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            server = TCP_IP, TCP_PORT
            sock.connect(server)
            print(f'Connection established {server}')
            print(f'Send data: {data_dict}')
            # sock.send(str(data_dict).encode('utf-8'))
            sock.send(data_parse.encode('utf-8'))

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())


def run_http_server(server_class=HTTPServer, handler_class=HTTPHandler):
    server_address = "", HTTP_PORT
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


def write_to_storage(data: any) -> None:
    from datetime import datetime

    # print(data, type(data))
    data_dict = {key: value for key, value in [
            el.split('=') for el in data.split('&')]}

    data_json = {}
    with open('./storage/data.json', "r+") as file:
        try:
            data_json = json.load(file)
        except json.JSONDecodeError:
            pass

        data_json[datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")] = data_dict

        file.seek(0)
        json.dump(data_json, file, indent=4)


def run_server(ip, port):
    def handle(sock: socket.socket, address: str):
        print(f'Connection established {address}')
        while True:
            received = sock.recv(1024)
            if not received:
                break
            data = received.decode('utf-8')
            print(f'Data received: {data}')
            if not data is None:
                write_to_storage(data)
        print(f'Socket connection closed {address}')
        sock.close()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((ip, port))
    server_socket.listen(10)
    print(f'Start server {server_socket.getsockname()}')
    with cf.ThreadPoolExecutor(10) as client_pool:
        try:
            while True:
                new_sock, address = server_socket.accept()
                client_pool.submit(handle, new_sock, address)
        except KeyboardInterrupt:
            print(f'Destroy server')
        finally:
            server_socket.close()


if __name__ == "__main__":
    run_server_HTTP = Thread(target=run_http_server)
    run_server_HTTP.start()

    run_server(TCP_IP, TCP_PORT)