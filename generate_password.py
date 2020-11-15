import tkinter as tk
from tkinter import ttk
import string
import pyperclip

from entry import ClipboardEntry
from window import Window
from scale_utils import TraceWriteCallbackOnChanged, ttk_scale_int
from security_utils import generate_random_string, is_weak_password

WEAK_PWD_MSG = "Your password may be weak..."
ARE_YOU_SURE_MSG = "Are you sure?"


def confirm_weak_password(password):
    ask_user = lambda: tk.messagebox.askokcancel(title="Weak password", message=WEAK_PWD_MSG, icon = tk.messagebox.WARNING)
    return not is_weak_password(password) or ask_user()

def confirm_once(title, password):
    message = ARE_YOU_SURE_MSG
    icon = tk.messagebox.INFO
    if is_weak_password(password):
        message = WEAK_PWD_MSG + '\n' + message
        icon = tk.messagebox.WARNING
    return tk.messagebox.askyesno(title=title, message=message, icon=icon)



class GeneratePassword(Window):
    MAX_LENGTH = 32
    
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
        self.var_length = tk.IntVar(value=12)
        self.var_length_trace = TraceWriteCallbackOnChanged(var=self.var_length, cmd=self.generate_pwd)
        
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
         pyperclip.copy(self.password.get())

    def select(self):
        if confirm_weak_password(self.password.get()):
            self.is_password_selected = True
            self.close()