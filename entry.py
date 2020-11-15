import tkinter as tk

from collections import namedtuple
from tkinter import ttk

        
class ClipboardEntry(ttk.Entry):
    MAX_HISTORY = 30
    HISTORY_ENTRY = namedtuple('History', ('data', 'pre_index', 'post_index'))
    
    class DataChangedInfo:
        def __init__(self, pre=None, post=tk.END):
            self.pre_index = pre
            self.post_index = post
        
        def reset(self):
            self.pre_index = None
            self.post_index = tk.END
            
        def str(self):
            return str(self.pre_index) + ', ' + str(self.post_index)
        
        def repr(self):
            pre, post = tuple(map(repr, (self.pre_index, self.post_index)))
            return f'DataChangedInfo({pre}, {post})'
    
    def __init__(self, parent, max_length=None, **kwargs):
        self.data_var = kwargs.pop('textvariable', tk.StringVar())
        self.max_length = max_length
        self.data_changed_info = ClipboardEntry.DataChangedInfo()
        super().__init__(parent, textvariable=self.data_var, **kwargs)
        
        self.history = [ClipboardEntry.HISTORY_ENTRY(self.data_var.get(), None, self.index(tk.INSERT))]
        self.redo_stack = []
        
        self.context_menu = self.create_menu()
        self.bind("<Button-3>", self._show_context_menu)
        self.bind("<Control-z>", self.undo)
        self.bind("<Control-y>", self.redo)
        self.bind("<Key>", self._on_key_pressed)
        self.data_var.trace('w', self._on_data_changed)
        self.focus = self.focus_set
        
    def create_menu(self):
        menu = tk.Menu(self, tearoff=False)
        menu.add_command(label="Cut")
        menu.add_command(label="Copy")
        menu.add_command(label="Paste")
        return menu
    
    def clear_history(self):
        self.history.clear()
        self.redo_stack.clear()
        self.history.append(ClipboardEntry.HISTORY_ENTRY(self.data_var.get(), None, self.index(tk.INSERT)))
    
    def insert(self, index, string):
        idx = index if index != tk.INSERT else self.index()
        self.data_changed_info.pre_index = idx
        self.data_changed_info.post_index = idx + len(string)
        super().insert(index, string)
    
    def delete(self, first, last=None):
        def fix_index(idx):
            if idx == tk.INSERT:
                return self.index()
            elif idx == tk.END:
                return len(self.data_var.get())
            return idx
        fst, lst = tuple(map(fix_index, (first, last)))
        length = lst - fst if lst is not None else 1
        self.data_changed_info.pre_index = fst + length
        self.data_changed_info.post_index = fst
        super().delete(first, last)
        
    def focus_set(self):
        self.icursor(self.history[-1].post_index)
        super().focus()
    
    def undo(self, event=None):
        if len(self.history) > 1:
            pre_index = self.history[-1].pre_index
            self.redo_stack.append(self.history.pop())
            self.data_var.set(self.history[-1].data)
            if pre_index is not None:
                self.icursor(pre_index)
            
    def redo(self, event=None):
        if self.redo_stack:
            self.history.append(self.redo_stack.pop())
            self.data_var.set(self.history[-1].data)
            self.icursor(self.history[-1].post_index)

    def _on_key_pressed(self, event=None):
        # guaranteed to happen before data_var trace callback (_on_data_changed)
        length_difference = len(self.data_var.get()) - len(self.history[-1].data)
        self.data_changed_info.pre_index = self.index(tk.INSERT) - length_difference
        self.data_changed_info.post_index = self.index(tk.INSERT)
        
    def _on_data_changed(self, *args):
        data = self.data_var.get()
        if data != self.history[-1].data:
            if self.max_length is None or len(data) <= self.max_length:
                hist_entry = ClipboardEntry.HISTORY_ENTRY(self.data_var.get(), self.data_changed_info.pre_index, self.data_changed_info.post_index)
                self.history.append(hist_entry)
                self.redo_stack.clear()
                if len(self.history) > ClipboardEntry.MAX_HISTORY + 1:
                    self.history.pop(0)
            else:
                self.data_var.set(self.history[-1].data)
                if self.data_changed_info.pre_index is not None:
                    self.icursor(self.data_changed_info.pre_index)
        self.data_changed_info.reset()
        
    def _show_context_menu(self, event):
        self.context_menu.entryconfigure("Cut", command=lambda: self.event_generate("<<Cut>>"))
        self.context_menu.entryconfigure("Copy", command=lambda: self.event_generate("<<Copy>>"))
        self.context_menu.entryconfigure("Paste", command=lambda: self.event_generate("<<Paste>>"))
        self.context_menu.post(event.x_root, event.y_root)
        

class NamedEntry(ttk.Frame):
    def __init__(self, parent, name, *args, **kwargs):
        super().__init__(parent)
        ttk.Label(self, text=name).pack(side=tk.LEFT)
        ClipboardEntry(self, *args, **kwargs).pack(side=tk.LEFT)
        
        

        
        

            


    
