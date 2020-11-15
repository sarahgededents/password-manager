import secrets
import string


def generate_random_string(length, charsets):
    chars = list(map(secrets.choice, set(charsets)))
    if len(chars) < length:
        merged_charset = list(set(''.join(charsets)))
        chars += [secrets.choice(merged_charset) for _ in range(length - len(chars))]
    secrets.SystemRandom().shuffle(chars)
    return ''.join(chars)[:length]

def generate_password(length):
    charsets = (string.ascii_uppercase, string.ascii_lowercase, string.digits, string.punctuation)
    return generate_random_string(length, charsets)

def generate_captcha_string():
    charset = string.ascii_lowercase + string.digits + "%#&?*!^@=<>+"
    return generate_random_string(6, charset)

def is_weak_password(pwd):
    weak_pwd = ['123456', '123456789', 'qwerty', '111111', 'password', '12345678', 'abc123', '1234567', 'password1', '123123']
    if pwd in weak_pwd or len(pwd) < 15:
        return True
    return False