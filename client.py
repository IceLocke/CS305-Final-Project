import socket

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.Util.Padding import pad, unpad

from secrets import token_hex


def parse_response(response):
    parts = response.split(b'\r\n\r\n')
    lines = parts[0].split(b'\r\n')

    status = lines[0].decode()

    headers = {}
    for line in lines[1:]:
        line = line.decode()
        key, val = line.split(':', 1)
        headers[key.strip()] = val.strip()

    body = parts[1] if parts[1] != b'' else None

    return status, headers, body


class EncryptManager:
    def __init__(self):
        bytes_key = token_hex(32).encode('utf-8')
        self.key = bytes_key[:16]
        self.iv = bytes_key[-16:]

    def encrypt(self, plaintext):
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        return cipher.encrypt(pad(plaintext, 16))

    def decrypt(self, ciphertext):
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        return unpad(cipher.decrypt(ciphertext), 16)


class Client:
    def __init__(self, url, port, user):
        self.manager = EncryptManager()
        self.url = url
        self.port = port
        self.sock = None
        self.headers = {'User-Client': user}
        self.cookies = {}
        self.body = None

    def send(self, method='HEAD', url='/', ver='HTTP/1.1'):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.url, self.port))
        if self.body is not None:
            self.headers['Content-Length'] = len(self.body)
        elif 'Content-Length' in self.headers:
            self.headers.pop('Content-Length')

        self.sock.send(f'{method} {url} {ver}\r\n'.encode('utf-8'))
        for key, val in self.headers.items():
            self.sock.send(f'{key}: {val}\r\n'.encode('utf-8'))
        if self.cookies != {}:
            self.sock.send(b'Cookie: ')
            self.sock.send('; '.join([f'{key}={value}' for (key, value) in self.cookies.items()]).encode('utf-8'))
            self.sock.send(b'\r\n')

        self.sock.send(b'\r\n')

        if self.body is not None:
            self.sock.send(self.body)

    def recv(self):
        response = b''
        rec = self.sock.recv(1024)
        while rec:
            response += rec
            rec = self.sock.recv(1024)
        self.sock.close()
        self.sock = None
        return response

    def handshake(self):
        request = 'HEAD / HTTP/1.1\r\n'
        self.headers['Request-Public-Key'] = '1'

        self.send()
        status, headers, body = parse_response(self.recv())

        self.cookies['encryption-session'] = headers['Set-Cookie'].split('=')[1].strip()
        public_key = body
        bytes_key = token_hex(64).encode('utf-8')
        self.headers.pop('Request-Public-Key')
        self.body = self.manager.key + b'\r\n' + self.manager.iv
        cipher = PKCS1_OAEP.new(RSA.import_key(public_key))
        self.body = cipher.encrypt(self.body)

        self.send()
        status, headers, body = parse_response(self.recv())
        print(self.manager.decrypt(body).decode())

        self.body = self.manager.encrypt(b'AES for both side.')

        self.send()
        status, headers, body = parse_response(self.recv())
        print(self.manager.decrypt(body).decode())


def main():
    client = Client('localhost', 8080, 'Artanisax')
    client.handshake()


if __name__ == '__main__':
    main()
