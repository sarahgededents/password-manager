import csv
import math
import string

from itertools import combinations
from security.utils import generate_random_string

# we make the hypothetis that a computer take 1 nanosecond/combination

CHARSETS = { string.ascii_lowercase: 'lower', string.ascii_uppercase: 'upper', string.digits: 'digits', string.punctuation: 'punctuation'}

def gen_pwd(length, charsets):
    password = generate_random_string(length, charsets)
    charsets_names = sorted(set(map(CHARSETS.get, charsets)))
    return { '_'.join(charsets_names) + f'_{length}': f'{password}' }

def gen_pwds(start_length, stop_length=None):
    assert start_length >= 4
    if not stop_length or stop_length < start_length:
        stop_length = start_length
    pwds = {}
    for length in range(start_length, stop_length + 1):
        for charsets_count in range(len(CHARSETS)):
            for charsets in combinations(CHARSETS.keys(), charsets_count+1):
                pwd = gen_pwd(length, charsets)
                pwds.update(pwd)
    return pwds

def multicomb(n, k):
    return math.comb(n+k-1, k)

def number_results(target):
    charsets = []
    if any(map(lambda c: c in string.ascii_lowercase, target)):
        charsets.append(string.ascii_lowercase)
    if any(map(lambda c: c in string.ascii_uppercase, target)):
        charsets.append(string.ascii_uppercase)
    if any(map(lambda c: c in string.digits, target)):
        charsets.append(string.digits)
    if any(map(lambda c: c in string.punctuation, target)):
        charsets.append(string.punctuation)

    alphabet = "".join(charsets)

    n = 0
    for length in range(len(target)):
        n += multicomb(len(alphabet), length) * math.factorial(length)
    return n

class TIME_IN_NS:
    NANOSECOND = 1
    SECOND = 10**9 * NANOSECOND
    MINUTE = 60 * SECOND
    HOUR = 60 * MINUTE
    DAY = 24 * HOUR
    YEAR = 365 * DAY


def convert_to(target):
    duration_ns = number_results(target)
    if duration_ns >= TIME_IN_NS.YEAR:
        duration = round(duration_ns / TIME_IN_NS.YEAR)
        time_ref = TIME_IN_NS.YEAR
        unit_string = 'year'
    elif duration_ns >= TIME_IN_NS.DAY:
        duration = round(duration_ns / TIME_IN_NS.DAY)
        time_ref = TIME_IN_NS.DAY
        unit_string = 'month'
    elif duration_ns >= TIME_IN_NS.HOUR:
        duration = round(duration_ns / TIME_IN_NS.HOUR)
        time_ref = TIME_IN_NS.HOUR
        unit_string = 'hour'
    elif duration_ns >= TIME_IN_NS.MINUTE:
        duration = round(duration_ns / TIME_IN_NS.MINUTE)
        time_ref = TIME_IN_NS.MINUTE
        unit_string = 'minute'
    elif duration_ns >= TIME_IN_NS.SECOND:
        duration = round(duration_ns / TIME_IN_NS.SECOND)
        time_ref = TIME_IN_NS.SECOND
        unit_string = 'second'
    else:
        duration = duration_ns
        time_ref = TIME_IN_NS.NANOSECOND
        unit_string = 'nanosecond'
    return duration, time_ref, unit_string


def build_results(path = "duration_brute_force_results.csv"):
    pwds = gen_pwds(4, 25)
    with open(path, "w", newline='') as f:
        writer = csv.writer(f, delimiter=',')
        writer.writerow(['category', 'length', 'duration', 'time_ref', 'password', 'strength'])
        for category, password in pwds.items():
            duration, time_ref, unit_string = convert_to(password)
            if time_ref == TIME_IN_NS.NANOSECOND or time_ref == TIME_IN_NS.SECOND or time_ref == TIME_IN_NS.MINUTE:
                strength = "very weak"
            if time_ref == TIME_IN_NS.HOUR:
                strength = "weak"
            if time_ref == TIME_IN_NS.DAY:
                strength = "ok"
            if time_ref == TIME_IN_NS.YEAR and duration < 10:
                strength = "good"
            if time_ref == TIME_IN_NS.YEAR and 500 > duration >= 10:
                strength = "strong"
            if time_ref == TIME_IN_NS.YEAR and duration >= 500:
                strength = "very strong"
            rspliter = category.rsplit("_", 1)
            writer.writerow([rspliter[0], rspliter[1], duration, unit_string,  password, strength])

if __name__ == '__main__':
    build_results()