import os.path
from functools import partial

class WordSet:
    def __init__(self, path='rocky_you.txt', already_padded=False, already_sorted=True, max_length=15, line_count=None):
        self.in_path = path
        self.open_file = partial(open, encoding='utf-8', errors='ignore')
        self.max_length = max_length
        if line_count:
            self._line_count = line_count
        if already_padded and already_sorted:
            self._out_path = path
        else:
            self._prepare_pad_lines(already_sorted)

    class _Lines:
        def __init__(self, file, line_length, line_count=None):
            self.file = file
            self.line_length = line_length
            self.line_count = line_count
            self.file.seek(0)

        def __len__(self):
            return self.line_count

        def __getitem__(self, item):
            if self.line_count is not None and item >= self.line_count:
                raise IndexError('line index out of range')
            self.file.seek(item * (self.line_length + 2)) # 2 is len('\r\n'), TODO: make more portable
            return self.file.read(self.line_length).rstrip('\0')

    def __enter__(self):
        self._file = self.open_file(self.out_path, 'r')
        return WordSet._Lines(self._file, self.line_length, self.line_count)

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self._file.close()
        self._file = None

    @property
    def out_path(self):
        if not hasattr(self, '_out_path'):
            name, _ = os.path.splitext(self.in_path)
            self._out_path = f'{name}.ws'
        return self._out_path

    @property
    def line_length(self):
        if not hasattr(self, '_line_length'):
            with self.open_file(self.out_path, 'r') as f:
                self._line_length = min(len(next(f).rstrip('\n')), self.max_length)
        return self._line_length

    @property
    def line_count(self):
        if not hasattr(self, '_line_count'):
            with self.open_file(self.out_path, 'r') as f:
                self._line_count = 0
                for line in f:
                    stripped_line = line.rstrip('\n')
                    if stripped_line and len(stripped_line) <= self.max_length:
                        self._line_count += 1
        return self._line_count

    def _prepare_pad_lines(self, already_sorted=True):
        with self.open_file(self.in_path, 'r') as f:
            self._line_length = max(map(len, map(lambda s: s.rstrip('\n'), f)))
            self._line_length = min(self.max_length, self._line_length)
        self._line_count = 0
        with self.open_file(self.in_path, 'r') as in_f:
            with self.open_file(self.out_path, 'w') as out_f:
                lines_iter = in_f if already_sorted else sorted(in_f)
                for line in lines_iter:
                    stripped_line = line.rstrip('\n')
                    if stripped_line and len(stripped_line) <= self.max_length:
                        padded_line = stripped_line + '\0' * (self._line_length - len(stripped_line)) + '\n'
                        out_f.write(padded_line)
                        self._line_count += 1

    def __contains__(self, item):
        min, max = 0, self.line_count
        with self as lines:
            while max > min:
                mid = (max - min) // 2 + min
                if item == lines[mid]:
                    return True
                if item < lines[mid]:
                    max = mid
                else:
                    min = mid + 1
        return False

    def __getitem__(self, item):
        with self as lines:
            return lines[item]

COMMON_PASSWORDS = WordSet('rockyou.ws', already_padded=True, line_count=14104409)