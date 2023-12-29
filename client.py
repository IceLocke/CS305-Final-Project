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
    
    print(status)
    print(headers)
    print(body)
    
    return status, headers, body


class EncryptManager:
    def __init__(self):
        self.key, self.iv = self.generate_key()
        
    
    def generate_key(self, magic=b'magic'):
        return pad(magic, 16), pad(magic + magic, 16)
    
    
    def encrypt(self, plaintext):
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        return cipher.encrypt(plaintext)
    
    
    def decrypt(self, session_id, ciphertext):
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        return cipher.decrypt(ciphertext)


class Client:
    def __init__(self, url, port, user):
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
            
        self.sock.send(f'{method} {url} {ver}\r\n'.encode('utf-8'))
        print(self.headers)
        for key, val in self.headers.items():
            self.sock.send(f'{key}: {val}\r\n'.encode('utf-8'))
        if self.cookies != {}:
            self.sock.send(b'Cookie: ')
            self.sock.send('; '.join([f'{key}={value}' for (key, value) in self.cookies.items()]).encode('utf-8'))
            self.sock.send(b'\r\n')
        
        if self.body is not None:
            print(self.body)
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
        aes_key, iv = bytes_key[:32], bytes_key[32:]
        self.headers.pop('Request-Public-Key')
        self.body = aes_key + b'\r\n' + iv
        cipher = PKCS1_OAEP.new(RSA.import_key(public_key))
        self.body = cipher.encrypt(self.body)
        self.send()
        
        status, headers, body = parse_response(self.recv())


def main():
    client = Client('localhost', 8080, 'Artanisax')
    client.handshake()
    
    
if __name__ == '__main__':
    main()
    