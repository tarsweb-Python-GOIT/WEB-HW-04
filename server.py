import socket
from concurrent import futures as cf

TCP_IP = 'localhost'
TCP_PORT = 5000


def write_to_storage(data: any) -> None:
    import json
    from datetime import datetime

    # print(data, type(data))
    data = json.loads(data)

    data_json = {}
    with open('./storage/data.json', "r+") as file:
        try:
            data_json = json.load(file)
        except json.JSONDecodeError:
            pass

        data_json[datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")] = data

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
    print(f'Start echo server {server_socket.getsockname()}')
    with cf.ThreadPoolExecutor(10) as client_pool:
        try:
            while True:
                new_sock, address = server_socket.accept()
                client_pool.submit(handle, new_sock, address)
        except KeyboardInterrupt:
            print(f'Destroy server')
        finally:
            server_socket.close()


if __name__ == '__main__':
    run_server(TCP_IP, TCP_PORT)
