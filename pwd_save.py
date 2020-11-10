import secrets
import string

from Crypto.Cipher import AES

def generate_password(length):
    string_char = string.ascii_letters + string.digits + string.punctuation
    pwd = secrets.choice(string_char)
    while len(pwd) != length:
        pwd += secrets.choice(string_char)
    
    char_list = list(pwd)
    secrets.SystemRandom().shuffle(char_list)
    pwd = ''.join(char_list)
    return pwd

def pad(key, lengths=(16,24,32)):
    if len(key) in lengths:
        return key
    target = next(filter(lambda l: l > len(key), lengths))
    return key + '\0' * (target - len(key))

class Encryption:
    def encrypt(self, data):
        data_bytes = pad(data).encode()
        return self._cipher().encrypt(data_bytes)
    
    def decrypt(self, data):
        data_bytes = data.encode() if isinstance(data, str) else data
        return self._cipher().decrypt(data_bytes).decode()
    
    def _cipher(self):
        return AES.new(pad(self.key))