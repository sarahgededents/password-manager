import secrets
import string

from Crypto.Cipher import AES

def generate_random_string(charset, length):
    chars = [secrets.choice(charset) for _ in range(length)]
    secrets.SystemRandom().shuffle(chars)
    return ''.join(chars)

def generate_password(length):
    charset = string.ascii_letters + string.digits + string.punctuation
    return generate_random_string(charset, length)

def generate_captcha_string():
    charset = string.ascii_lowercase + string.digits + "%#&?*!^@=<>+"
    return generate_random_string(charset, length=6)
    

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