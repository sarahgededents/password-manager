import tkinter as tk
from tkinter import ttk
from collections import namedtuple

root = tk.Tk()

class DotDict(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

PWD_STR_TUPLE = namedtuple('Strength', ('value', 'color', 'weight'))
_PWD_STRENGTH = [ ('VERY_WEAK', 'red', .4), ('WEAK', 'orange', 1.1), ('GOOD', 'yellow', .8), ('STRONG', 'green', .5) ]
PWD_STRENGTH = DotDict({ strength: PWD_STR_TUPLE(value+1, color, weight) for (value, (strength, color, weight)) in enumerate(_PWD_STRENGTH) })

def pwd_strength_to_string(pwd_strength):
    if isinstance(pwd_strength, int):
        pwd_strength = _PWD_STRENGTH[pwd_strength][0]
    return pwd_strength[0] + pwd_strength.replace('_', ' ').lower()[1:]

class PasswordStrength(ttk.Frame):
    class Bar(tk.Canvas):
        RECTANGLE_TUPLE = namedtuple('Rectangle', ('id', 'value', 'start', 'end', 'color'))

        def __init__(self, parent, width=200, height=30, singlemode=True):
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
        self.bar = PasswordStrength.Bar(self, singlemode=False)
        self.bar.pack(expand=True, fill=tk.BOTH)
        password_var.trace('w', lambda *args: self.update(password_var.get()))

    def update(self, password):
        self.bar.set_value(len(password))

pwd = tk.StringVar()
PasswordStrength(root, pwd).pack(expand=True, fill=tk.BOTH)
tk.Entry(root, textvariable=pwd).pack()
root.mainloop()