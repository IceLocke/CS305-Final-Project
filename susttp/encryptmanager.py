from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.Util.Padding import pad, unpad

from susttp.request import Request
import susttp.response as resp

from secrets import token_hex


class EncryptManager:
    def __init__(self, magic=2048):
        self.key = RSA.generate(magic)
        self.private_key = self.key.export_key()
        self.public_key = self.key.publickey().export_key()
        self.ase_keys = {} # <session_id>: (<key>, <iv>)
            
    
    def get_RSA_public(self):
        return self.public_key
        
    
    def decrypt_RSA(self, ciphertext):
        cipher = PKCS1_OAEP.new(RSA.import_key(self.private_key))
        return cipher.decrypt(ciphertext)
    
    
    def add_aes_key(self, session_id, aes_key, iv):
        self.aes_key[session_id] = (aes_key, iv)
    
    
    def encrypt_AES(self, session_id, plaintext):
        aes_key, iv = self.aes_key[session_id]
        cipher = AES.new(aes_key, AES.MODE_CBC, iv)
        return cipher.encrypt(plaintext)
    
    
    def decrypt_AES(self, session_id, ciphertext):
        aes_key, iv = self.aes_key[session_id]
        cipher = AES.new(aes_key, AES.MODE_CBC, iv)
        return cipher.decrypt(ciphertext)
    
    
    def handle_request(self, request: Request):
        if ('Request-Public-Key', '1') in request.headers.items():
            session_id = str(token_hex(32))
            self.ase_keys[session_id] = None
            response = resp.Response(body=self.get_RSA_public())
            response.headers['Public-Key'] = '1'
            return response
        else:
            session_id = request.cookies['encryption-session']
            key, iv = unpad(self.decrypt_RSA(request.body)).decode().split('\r\n')
            self.ase_keys[session_id] = (key, iv)
            return resp.Response()
    
    
    def in_process(self, request: Request):
        print(request.headers)
        if ('Request-Public-Key', '1') in request.headers.items():
            return True
        elif 'encryption-session' in request.cookies:
            session_id = request.cookies['encryption-session']
            if self.ase_keys[session_id] is None:
                return True
        return False
    
    
    def decrypt_request(self, session_id, request: Request):
        if request.body:
            request.body = self.decrypt_AES(request.body)
    
    
    def encyrpt_response(self, seesion_id, response: resp.Response):
        if response.body is not None:
            response.body = self.decrypt_AES(response.body)
            if 'Content-Length' in response.headers:
                response.headers['Content-Length'] = len(response.body)

    