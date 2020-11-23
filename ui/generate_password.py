import tkinter as tk
from tkinter import ttk
import string

from ui.context_menu import copy_to_clipboard
from ui.entry import ClipboardEntry
from security.password_strength import PasswordStrength
from ui.scale_utils import TraceWriteCallbackOnChanged, ttk_scale_int
from security.utils import generate_random_string
from ui.window import Window

ARE_YOU_SURE_MSG = "Are you sure?"

def confirm_once(title, password):
    message = ARE_YOU_SURE_MSG
    icon = tk.messagebox.INFO
    return tk.messagebox.askyesno(title=title, message=message, icon=icon)

class GeneratePassword(Window):
    MAX_LENGTH = 128
    
    def show_dialog(parent):
        dialog = GeneratePassword(parent)
        return dialog.password.get() if dialog.is_password_selected else None

    def __init__(self, parent):
        super().__init__(parent, title="Random Password Generator")
    
    def _body(self, master):
        self.is_password_selected = False
        self.password = tk.StringVar(value="")
        self.var_lower = tk.BooleanVar(value=True)
        self.var_upper = tk.BooleanVar(value=True)
        self.var_digit = tk.BooleanVar(value=True)
        self.var_punct = tk.BooleanVar(value=False) 
        self.var_length = tk.IntVar(value=16)
        self.var_length_trace = TraceWriteCallbackOnChanged(var=self.var_length, cmd=self.generate_pwd)

        self.var_lower.trace("w", self.generate_pwd)
        self.var_upper.trace("w", self.generate_pwd)
        self.var_digit.trace("w", self.generate_pwd)
        self.var_punct.trace("w", self.generate_pwd)

        self.resizable(False, False)
        frame_top = ttk.Frame(master)
        ttk.Button(frame_top, text="Copy", command=self.copy).pack(side=tk.LEFT)
        ttk.Label(frame_top, text="Password Generator", font="TkDefaultFont 12 bold").pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(frame_top, text="Select", command=self.select).pack(side=tk.LEFT)
        frame_top.pack(fill=tk.X)
        
        frame_generate = ttk.Frame(master)
        self.entry = ClipboardEntry(frame_generate, width=38, max_length=GeneratePassword.MAX_LENGTH, textvariable=self.password)
        self.entry.grid(row=0)
        ttk.Button(frame_generate, text="Generate", command=self.generate_pwd).grid(row=0, column=1)
        frame_weak = PasswordStrength(frame_generate, self.password)
        frame_weak.grid(row=1)
        frame_generate.pack(fill=tk.X)


        frame_length = ttk.Frame(master)
        tk.Label(frame_length, text="Length").grid(row=0, column=0)
        ttk.Scale(frame_length, variable=self.var_length, from_=5, to=GeneratePassword.MAX_LENGTH, orient=tk.HORIZONTAL, command=ttk_scale_int(self.var_length), length=200).grid(row=0, column=1)
        ttk.Label(frame_length, textvariable=self.var_length).grid(row=0, column=2)
        frame_length.pack(fill=tk.X)
        
        frame_check = ttk.Frame(master)
        ttk.Checkbutton(frame_check, text="abc", variable=self.var_lower).grid(row=0, column=0)
        ttk.Checkbutton(frame_check, text="ABC", variable=self.var_upper).grid(row=0, column=1)
        ttk.Checkbutton(frame_check, text="123", variable=self.var_digit).grid(row=0, column=2) 
        ttk.Checkbutton(frame_check, text="@#%", variable=self.var_punct).grid(row=0,column=3)
        frame_check.pack(fill=tk.X)

        self.generate_pwd()
        return self.entry
        
    def generate_pwd(self, *args):
        length = self.var_length.get()
        charsets = []
        if self.var_lower.get():
            charsets.append(string.ascii_lowercase)
        if self.var_upper.get():
            charsets.append(string.ascii_uppercase)
        if self.var_digit.get():
            charsets.append(string.digits)
        if self.var_punct.get():
            charsets.append(string.punctuation)
        if charsets:
            self.password.set(generate_random_string(length, charsets))
            self.entry.focus()
      
    def copy(self): 
        copy_to_clipboard(self.tk, self.password.get())

    def select(self):
        self.is_password_selected = True
        self.close()