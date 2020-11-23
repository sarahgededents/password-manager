from collections import namedtuple

import sqlite3
import os
import hashlib

class EmptyCM:
    def __enter__(self):
        return None

    def __exit__(self, *args):
        pass

class CancelOperation(BaseException):
    pass

class Cursor:
    def __init__(self, path, name=''):
        self.name = name
        self.path = path
        self._nesting = 0

    def __enter__(self):
        if not self._nesting:
            self.connection = sqlite3.connect(self.path)
            self.cursor = self.connection.cursor()
        self._nesting += 1
        return self
        
    def __exit__(self, exc_type, exc_value, exc_traceback):
        self._nesting -= 1
        if not self._nesting:
            if exc_type is None:
                self.connection.commit()
            self.connection.close()
            if exc_type == CancelOperation:
                return True

    @staticmethod
    def cancel():
        raise CancelOperation()

    def execute(self, *args, **kwargs):
        return self.cursor.execute(*args, **kwargs)
    
    def fetch(self, *args, **kwargs):
        self.cursor.execute(*args, **kwargs)
        return self.cursor.fetchall()

SALT_LENGTH=32
def hash_password(pwd, salt):
    return hashlib.pbkdf2_hmac(
        'sha256',
        pwd.encode('utf-8'),
        salt,
        100000, # It is recommended to use at least 100,000 iterations of SHA-256 
        dklen=128 # Get a 128 byte key
    )

class Error:
    def __init__(self, message=""):
        self.message = message
        
    def __bool__(self):
        return False
    
    def __str__(self):
        return str(self.message)
    
    def __repr__(self):
        return f"Error(message={self.message})"

class DatabaseManager:
    def __init__(self, path):
        self.path = path
        with self.cursor() as cursor:
            cursor.execute(""" CREATE TABLE IF NOT EXISTS manager (
                                name text PRIMARY KEY,
                                email text,
                                password text,
                                website text
                                )
            """) # todo, build from FIELDS
            cursor.execute(""" CREATE TABLE IF NOT EXISTS master_pwd (hashed_password text)""")
        self.on_submit = []
        self.on_update = []
        self.on_delete = []
            
    ROW_TUPLE = namedtuple("Row", ('name', 'email', 'password', 'website')) # todo: build from FIELDS, reuse same gen func with Form?
    
    def cursor(self, existing_cursor=None, name=''):
        return Cursor(self.path, name) if existing_cursor is None else existing_cursor
    
    def _get_master_pwd_hash(self):
        with self.cursor() as cursor:
            hash_in_list = cursor.fetch("SELECT * FROM master_pwd LIMIT 1")
        return hash_in_list[0][0] if hash_in_list else None

    def set_master_pwd(self, password):
        salt = os.urandom(SALT_LENGTH)
        key = hash_password(password, salt)
        stored_hash = salt + key
        with self.cursor() as cursor:
            if cursor.fetch("SELECT * FROM master_pwd LIMIT 1"):
                cursor.execute("UPDATE master_pwd SET hashed_password = :hash", {'hash': stored_hash})
            else:
                cursor.execute("INSERT INTO master_pwd VALUES (:hash)", {'hash': stored_hash})

    def check_master_pwd(self, password):
        stored_hash = self._get_master_pwd_hash()
        if stored_hash is None:
            return False
        salt, key = stored_hash[:SALT_LENGTH], stored_hash[SALT_LENGTH:]
        return key == hash_password(password, salt)
    
    def has_master_pwd(self):
        return self._get_master_pwd_hash() is not None

    def fetch_all(self):
        with self.cursor() as cursor:
            all_rows = cursor.fetch("SELECT * FROM manager")
        return map(lambda row: DatabaseManager.ROW_TUPLE(*row), all_rows)
    
    def fetch_one(self, name):
        with self.cursor() as cursor:
            rows = cursor.fetch("SELECT * FROM manager WHERE name = :name LIMIT 1", {'name': name})
        return DatabaseManager.ROW_TUPLE(*rows[0]) if rows else None
    
    def exists(self, name):
        with self.cursor() as cursor:
            return bool(cursor.fetch("SELECT name FROM manager WHERE name = :name", {'name': name}))

    def submit(self, fields, cursor=None):
        if not fields.name:
            return Error("Please fill in a name!")
        with self.cursor(cursor) as cursor:
            cursor.execute("INSERT INTO manager VALUES (:name, :email, :password, :website)",
                {
                    'name': fields.name,
                    'email': fields.email,
                    'password': fields.password,
                    'website': fields.website,
                }
            )
        for callback in self.on_submit:
            callback(fields)
        return True


    def delete(self, name, cursor=None):
        if not name:
            return Error("Please fill in a name!")
        with self.cursor(cursor) as cursor:
            cursor.execute("DELETE FROM manager WHERE manager.name = :name", { 'name': name })
        for callback in self.on_delete:
            callback(name)
        return True


    def update(self, fields, cursor=None):
        if not fields.name:
            return Error("Please fill in a name!")
        with self.cursor(cursor) as cursor:
            cursor.execute("UPDATE manager SET email = :email, password = :password, website = :website WHERE name = :name",
                           {
                               'name': fields.name,
                               'email': fields.email,
                               'password': fields.password,
                               'website': fields.website,
                            }
                        ) #sanitize
        for callback in self.on_update:
            callback(fields)
        return True

    def recipher(self, decrypt, encrypt):
        with self.cursor(name="recipher") as cursor:
            for row in self.fetch_all():
                new_row = row._replace(password=encrypt(decrypt(row.password)))
                self.update(new_row, cursor=cursor)
