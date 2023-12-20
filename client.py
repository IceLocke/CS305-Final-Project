import socket
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.Util.Padding import pad, unpad


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
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((url, port))
        self.headers = {'User-Client': user}        


    def send(self, method='HEAD', url='/', ver='HTTP/1.1', body=None):
        print(f'{method} {url} {ver}\r\n')
        self.sock.send(f'{method} {url} {ver}\r\n'.encode('utf-8'))
        for key, val in self.headers.items():
            print(f'{key}: {val}\r\n')
            self.sock.send(f'{key}: {val}\r\n'.encode('utf-8'))
        self.sock.send(b'\r\n')
        if body is not None:
            print(body)
            self.sock.send(body)
    
    
    def recv(self):
        response = b''
        rec = self.sock.recv(1024)
        while rec:
            response += rec
            rec = self.sock.recv(1024)
        return response

    
    def handshake(self):
        request = 'HEAD / HTTP/1.1\r\n'
        self.headers['Request-Public-Key'] = '1'
        self.send()
        response = parse_response(self.recv())


def main():
    client = Client('localhost', 8080, 'Artanisax')
    client.handshake()
    
    
if __name__ == '__main__':
    main()
    