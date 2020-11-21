import center_tk_window
import tkinter as tk
import abc

from tkinter import ttk


class Window(tk.Toplevel, metaclass=abc.ABCMeta):
    def __init__(self, parent, title):
        super().__init__(parent)

        self.withdraw() # disappear for now
        if parent.winfo_viewable():
            self.transient(parent)
        self.title(title)
        self.parent = parent

        body_frame = ttk.Frame(self)
        self.initial_focus = self._body(body_frame)
        body_frame.pack(fill=tk.BOTH, expand=True)
        
        if hasattr(self, '_buttonbox') and callable(self._buttonbox):
            self._buttonbox()

        if not self.initial_focus:
            self.initial_focus = self
        self.protocol("WM_DELETE_WINDOW", self.close)
        if self.parent is not None:
            center_tk_window.center_on_parent(parent, self)
        self.deiconify() # appear
        self.initial_focus.focus_set()
        self.wait_visibility()
        self.grab_set()
        self.wait_window(self)

    @abc.abstractmethod
    def _body(self, frame):
        pass

    def destroy(self):
        self.initial_focus = None
        super().destroy()
        
    def close(self):
        self.destroy()