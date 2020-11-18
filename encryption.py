import cryptography.fernet
import base64
import cryptography.hazmat.primitives.kdf.pbkdf2 as key_derivation
import cryptography.hazmat.backends
from cryptography.hazmat.primitives import hashes
from funcy import compose

import os


class DummyCipher:
    @staticmethod
    def has_password():
        return False

    def clear_password(self):
        pass

    @staticmethod
    def encrypt(data_bytes):
        return data_bytes

    @staticmethod
    def decrypt(data_bytes):
        return data_bytes


class FernetPasswordCipher:
    SALT_LENGTH = 32
    KDF_ITERATIONS = 100000

    def __init__(self, password):
        if isinstance(password, str):
            password = password.encode()
        self._password = bytearray(password)

    def has_password(self):
        return self._password is not None

    def clear_password(self):
        self._password[:] = b'\0' * len(self._password)
        self._password = None

    def _derive_key(self, salt):
        if not self.has_password():
            raise ValueError("FernetPasswordCipher: No password currently set, cannot derive key")
        key_derivator = key_derivation.PBKDF2HMAC(
            algorithm=hashes.SHA256(), length=32, salt=salt, iterations=FernetPasswordCipher.KDF_ITERATIONS,
            backend=cryptography.hazmat.backends.default_backend()
        )
        pwd_to_key = compose(base64.urlsafe_b64encode, key_derivator.derive)
        return pwd_to_key(self._password)  # cryptography.Fernet expects a URL-safe base64-encoded 32-byte key

    def encrypt(self, data_bytes):
        salt = os.urandom(FernetPasswordCipher.SALT_LENGTH)
        key = self._derive_key(salt)
        return salt + cryptography.fernet.Fernet(key).encrypt(data_bytes)

    def decrypt(self, encrypted_data):
        salt_length = FernetPasswordCipher.SALT_LENGTH
        salt, data_bytes = encrypted_data[:salt_length], encrypted_data[salt_length:]
        try:
            key = self._derive_key(salt)
            return cryptography.fernet.Fernet(key).decrypt(data_bytes)
        except (cryptography.fernet.InvalidToken, TypeError, AttributeError):
            return None
        except BaseException as e:
            print(str(e))
            return None


class Encryption:
    def __init__(self, db, cipher_type=FernetPasswordCipher):
        self._db = db
        self._cipher = DummyCipher()
        self._cipher_type = cipher_type

    @property
    def password(self):
        return self._cipher.has_password()

    @password.setter
    def password(self, pwd):
        if self.password:
            self._update_password(pwd)
        else:
            self._load_password(pwd)

    def _load_password(self, pwd):
        self._set_cipher(self._cipher_type(pwd))

    def _update_password(self, pwd):
        old_cipher, new_cipher = self._cipher, self._cipher_type(pwd)
        self._db.recipher(decrypt=old_cipher.decrypt, encrypt=new_cipher.encrypt)
        self._set_cipher(new_cipher)

    def _set_cipher(self, cipher):
        self._cipher.clear_password()
        self._cipher = cipher

    def encrypt(self, data):
        data_bytes = data.encode()
        return self._cipher.encrypt(data_bytes)

    def decrypt(self, encrypted_data, report_error_func=print):
        decrypted = self._cipher.decrypt(encrypted_data)
        if decrypted is None:
            report_error_func("Unable to decrypt data. Database may be corrupted.")
            return ''
        return decrypted.decode()
