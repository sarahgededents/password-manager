import os.path
from functools import partial


def can_decode(bytes_, encoding='utf-8'):
    try:
        bytes_.decode(encoding, errors="strict")
        return True
    except UnicodeDecodeError:
        return False


def prepare_wordset(in_path, out_path=None, is_sorted=False, min_length=1, max_length=16):
    out_path = out_path or (os.path.splitext(in_path)[0] + '.ws')
    words = partial(map, lambda line: line.rstrip(b'\r\n'))
    word_length, word_count = 0, 0
    with open(in_path, 'rb') as in_f:
        in_words = filter(lambda w: w and min_length <= len(w) <= max_length and can_decode(w), words(in_f))
        for word in in_words:
            word_length = max(len(word), word_length or 0)
            word_count += 1
        with open(out_path, 'wb') as out_f:
            out_f.write(b"%d %d\n" % (word_length, word_count))
            in_f.seek(0)
            for word in (in_words if is_sorted else sorted(in_words)):
                block = word + b'\0' * (word_length - len(word))
                out_f.write(block)


class WordSet:
    class _Words:
        def __init__(self, file, offset, word_length, word_count):
            self.file = file
            self.offset = offset
            self.word_length = word_length
            self.word_count = word_count

        def __len__(self):
            return self.word_count

        def __getitem__(self, index):
            if self.word_count is not None and index >= self.word_count:
                raise IndexError('word index out of range')
            self.file.seek(self.offset + index * self.word_length)
            return self.file.read(self.word_length).decode('utf-8').rstrip('\0')

    def __init__(self, path):
        try:
            with open(path, 'rb') as f:
                self._word_length, self._word_count = map(int, f.readline().split())
                self._offset = f.tell()
            self._path = path
        except (FileNotFoundError, ValueError):
            self._path = None
            pass

    def __enter__(self):
        self._file = open(self.path, 'rb')
        return self._Words(self._file, self._offset, self.word_length, self.word_count)

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self._file.close()
        self._file = None

    def __bool__(self):
        return self.path is not None

    @property
    def path(self):
        return self._path

    @property
    def word_length(self):
        return self._word_length

    @property
    def word_count(self):
        return self._word_count

    def __contains__(self, item):
        if self:
            min_idx, max_idx = 0, self.word_count
            with self as words:
                while max_idx > min_idx:
                    mid_idx = (max_idx - min_idx) // 2 + min_idx
                    mid_word = words[mid_idx]
                    if item == mid_word:
                        return True
                    elif item < mid_word:
                        max_idx = mid_idx
                    else:
                        min_idx = mid_idx + 1
        return False

    def __getitem__(self, item):
        with self as words:
            return words[item]


