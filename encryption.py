PADDING_CHAR = '\0'
def pad(key, lengths=(16,24,32)):
    if len(key) in lengths:
        return key
    target = next(filter(lambda l: l > len(key), lengths))
    return key + PADDING_CHAR * (target - len(key))


class DummyCipher:
    def encrypt(self, data, *args, **kwargs):
        return data

    def decrypt(self, data, *args, **kwargs):
        return data

class Encryption:
    @property
    def key(self):
        return hasattr(self, '_cipher')
       
    @key.setter
    def key(self, val):
        self._cipher = DummyCipher()
    
    def encrypt(self, data):
        if self.key:
            data_bytes = pad(data).encode()
            return self._cipher.encrypt(data_bytes)
    
    def decrypt(self, data_bytes):
        if self.key and data_bytes is not None:
            padded_data = self._cipher.decrypt(data_bytes).decode()
            return padded_data.rstrip(PADDING_CHAR)