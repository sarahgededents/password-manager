import tkinter as tk

from captcha_ import Captcha
from private_entry import PrivateEntry
from tkinter import messagebox
from tkinter import ttk
from window import Window
from password_strength import PasswordStrength

class MasterDialog(Window):
    class Mode:
        CHECK = 0
        SET = 1

    def __init__(self, parent, db, encryption, mode=Mode.CHECK):
        self.db = db
        self.encryption = encryption
        self.mode = mode if self.db.has_master_pwd() else MasterDialog.Mode.SET
        super().__init__(parent, title="Master password")
        
    def close(self):
        self.cancel()

    def _body(self, master):
        self.resizable(False, False)
        verb = self._get_verb()
        ttk.Label(master, text=f"{verb} master password:").grid(row=0)
        pwd = tk.StringVar()
        self.entry = PrivateEntry(master, textvariable=pwd, width=38)
        self.entry.grid(row=1)
        self.label = ttk.Label(master)
        if self.mode == MasterDialog.Mode.SET:
            ttk.Label(master, text="Confirm master password:").grid(row=2)
            self.entry2 = PrivateEntry(master, width=38)
            self.entry2.grid(row=3)
            frame = PasswordStrength(master, pwd)
            frame.grid(row=4)
        if self.mode == MasterDialog.Mode.CHECK:
            self.captcha = Captcha(master)
            self.captcha.grid(row=2)

        return self.entry
    
    def _buttonbox(self):
        box = ttk.Frame(self)

        ttk.Frame(box).pack(side=tk.LEFT, fill=tk.X, expand=True)
        w = ttk.Button(box, text="OK", width=10, command=self.ok, default=tk.ACTIVE)
        w.pack(side=tk.LEFT)
        w = ttk.Button(box, text="Cancel", width=10, command=self.cancel)
        w.pack(side=tk.LEFT)
        ttk.Frame(box).pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

        box.pack(fill=tk.BOTH, expand=True)
    
    def ok(self, event=None):
        if not self.validate():
            if self.mode == MasterDialog.Mode.CHECK:
                self.captcha.refresh()
                self.entry.delete(0, tk.END)
            self.initial_focus.focus()
            return
            
        self.withdraw()
        self.update_idletasks()
            
        self.apply()

        self.parent.focus_set()
        self.destroy()
        
    def cancel(self, event=None):
        if self._is_changing_password():
            self.parent.focus_set()
            self.destroy()
        else:
            self.parent.destroy()
    
    def apply(self):
        if self.mode == MasterDialog.Mode.SET:
            try:
                self.encryption.password = self.entry.get()
                self.db.set_master_pwd(self.entry.get())
            except:
                messagebox.showerror(title="Failure", message=f"Failed to set master password. Operation aborted.")
                raise
        else:
            self.encryption.password = self.entry.get()

    def validate(self):
        self.label.grid_forget()
        ok = True

        if self.mode == MasterDialog.Mode.CHECK:   
            if not self.captcha.validate():
                self.label.configure(text="Invalid captcha!")
                ok = False
            elif not self.db.check_master_pwd(self.entry.get()):
                self.label.configure(text="Invalid password!")
                ok = False
        elif self.mode == MasterDialog.Mode.SET:
            if self.entry.get() != self.entry2.get():
                self.label.configure(text="Passwords don't match!")
                ok = False

        if not ok and self.mode == MasterDialog.Mode.CHECK:
            self.label.grid(row=3)
        if not ok and self.mode == MasterDialog.Mode.SET:
            self.label.grid(row=5)

        return ok

    def _is_changing_password(self):
        return self.mode == MasterDialog.Mode.SET and self.db.has_master_pwd()
    
    def _get_verb(self):
        if self.mode == MasterDialog.Mode.CHECK:
            return "Enter"
        elif self.mode == MasterDialog.Mode.SET:
            return "Set new" if self._is_changing_password() else "Set"
        return "Enter"