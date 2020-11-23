import tkinter as tk

from ui.entry import ClipboardEntry
from tkinter import ttk

class PrivateEntry(ttk.Frame):
    def __init__(self, master, width=20, **kwargs):
        super().__init__(master)
        self.is_showing_stars = tk.BooleanVar(self, value=True)
        self.entry = ClipboardEntry(self, width=width-3, **kwargs)
        self.checkbox = ttk.Checkbutton(self, onvalue=False, offvalue=True, variable=self.is_showing_stars)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.checkbox.pack(side=tk.RIGHT)
        self._update_show_stars()
        self.is_showing_stars.trace('w', self._update_show_stars)
        
    def clear_history(self):
        self.entry.clear_history()
        
    def bind(self, *args, **kwargs):
        return self.entry.bind(*args, **kwargs)
    
    def focus(self):
        return self.entry.focus()
    
    def focus_set(self):
        return self.entry.focus_set()
        
    def get(self, *args, **kwargs):
        return self.entry.get(*args, **kwargs)
        
    def delete(self, *args, **kwargs):
        return self.entry.delete(*args, **kwargs)
    
    def _update_show_stars(self, *args):
        show = "*" if self.is_showing_stars.get() else ""
        self.entry.config(show=show)