import tkinter as tk
from tkinter import ttk
from collections import namedtuple
from security.word_set import WordSet
from security.time_cracker import number_results, TIME_IN_NS

COMMON_PASSWORDS_LENGTH_9_TO_16 = WordSet('rockyou_9-16.ws')

def compute_password_strength(pwd):
    if not pwd:
        return 0
    if pwd in COMMON_PASSWORDS_LENGTH_9_TO_16:
        return PWD_STRENGTH.VERY_WEAK.value
    number_combinations = number_results(pwd)
    if number_combinations < TIME_IN_NS.HOUR:
        return PWD_STRENGTH.VERY_WEAK.value
    elif number_combinations < TIME_IN_NS.DAY:
        return PWD_STRENGTH.WEAK.value
    elif number_combinations < TIME_IN_NS.YEAR:
        return PWD_STRENGTH.OK.value
    elif number_combinations < 10 * TIME_IN_NS.YEAR:
        return PWD_STRENGTH.GOOD.value
    elif number_combinations < 500 * TIME_IN_NS.YEAR:
        return PWD_STRENGTH.STRONG.value
    else:
        return PWD_STRENGTH.VERY_STRONG.value

class DotDict(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


PWD_STR_TUPLE = namedtuple('Strength', ('value', 'color', 'weight'))
_PWD_STRENGTH = [ ('VERY_WEAK', 'orange red', .8), ('WEAK', 'dark orange', .8), ('OK', 'orange', .8), ('GOOD', 'gold', .8), ('STRONG', 'yellow green', .8), ('VERY_STRONG', 'sea green', .8) ]
PWD_STRENGTH = DotDict({ strength: PWD_STR_TUPLE(value+1, color, weight) for (value, (strength, color, weight)) in enumerate(_PWD_STRENGTH) })

def pwd_strength_to_string(pwd_strength):
    if isinstance(pwd_strength, int):
        pwd_strength = _PWD_STRENGTH[pwd_strength][0]
    return pwd_strength[0] + pwd_strength.replace('_', ' ').lower()[1:]

class PasswordStrength(ttk.Frame):
    class Bar(tk.Canvas):
        RECTANGLE_TUPLE = namedtuple('Rectangle', ('id', 'value', 'start', 'end', 'color'))

        def __init__(self, parent, width=230, height=12, singlemode=True):
            super().__init__(parent, width=width, height=height)
            self.width, self.height = width, height
            self.singlemode = singlemode
            total_weight = sum(map(lambda strength: strength.weight, PWD_STRENGTH.values()))
            def _strength_to_rectangle(strength):
                id, start = -1, 0
                return PasswordStrength.Bar.RECTANGLE_TUPLE(id, strength.value, start, width * strength.weight / total_weight, strength.color)

            rectangles = []
            current_width = 0
            for desc in map(_strength_to_rectangle, PWD_STRENGTH.values()):
                shifted = desc._replace(start=desc.start + current_width, end=desc.end + current_width)
                current_width += desc.end
                rectangles.append(shifted)
            rectangles[-1] = (lambda desc: desc._replace(end=width))(rectangles[-1])

            starty, endy = (0, self.height)
            self.rectangles = []
            for rect in rectangles:
                startx = 0 if self.singlemode else rect.start
                rect_id = self.create_rectangle(startx, starty, rect.end, endy, fill='', outline='')
                self.rectangles.append(rect._replace(id=rect_id))
            self.text_id = self.create_text(width/2, height/2, text="")

        def set_value(self, val):
            val = min(val, len(self.rectangles))
            for rect in self.rectangles:
                show = rect.value == val if self.singlemode else rect.value <= val
                fill = rect.color if show else ''
                self.itemconfig(rect.id, fill=fill)
            text = '' if not val else _PWD_STRENGTH[val-1][0].replace('_', ' ').lower()
            self.itemconfig(self.text_id, text=text)

    def __init__(self, parent, password_var):
        super().__init__(parent)
        self.var = tk.IntVar()
        self.bar = PasswordStrength.Bar(self, singlemode=True)
        self.bar.pack(expand=True, fill=tk.BOTH)
        password_var.trace('w', lambda *args: self.update_bar(password_var.get()))

    def update_bar(self, password):
        self.bar.set_value(compute_password_strength(password))