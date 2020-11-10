from collections import namedtuple

import sqlite3
import os
import hashlib

class Cursor:
    def __init__(self, path):
        self.path = path

    def __enter__(self):
        self.connection = sqlite3.connect(self.path)
        self.cursor = self.connection.cursor()
        return self
        
    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.connection.commit()
        self.connection.close()
        
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
            
    ROW_TUPLE = namedtuple("Row", ('name', 'email', 'password', 'website')) # todo: build from FIELDS, reuse same gen func with Form?

    
    def cursor(self):
        return Cursor(self.path)
    
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

    def submit(self, fields):
        if fields.name and fields.email and fields.password and fields.website:
            with self.cursor() as cursor:
                cursor.execute("INSERT INTO manager VALUES (:name, :email, :password, :website)",
                    {
                        'name': fields.name,
                        'email': fields.email,
                        'password': fields.password, #encrypt_pwd(fields.password), #to maintain
                        'website': fields.website,
                    }
                )
            if (hasattr(self, 'on_submit')):
                self.on_submit(fields)
            return True, ""
        else:
            return False, "Please fill all details!"


    def delete(self, name):
        if name is not None:
            with self.cursor() as cursor:
                cursor.execute("DELETE FROM manager WHERE manager.name = :name", { 'name': name })
            if (hasattr(self, 'on_delete')):
                self.on_delete(name)
            return True, ""
        else:
            return False, "Please enter record id to delete!"


    def update(self, fields):
        if fields.name is not None:
            with self.cursor() as cursor:
                cursor.execute("UPDATE manager SET email = :email, password = :password, website = :website WHERE name = :name",
                               {
                                   'name': fields.name,
                                   'email': fields.email,
                                   'password': fields.password, #encrypt_pwd(fields.password), #to maintain
                                   'website': fields.website,
                                }
                            ) #sanitize
            if (hasattr(self, 'on_update')):
                self.on_update(fields)
            return True, ""
        else:
            return False, "Please enter fill all details!"