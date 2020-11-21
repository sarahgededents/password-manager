import tkinter as tk

from captcha_ import Captcha
from private_entry import PrivateEntry
from tkinter import messagebox
from tkinter import ttk
from window import Window
from password_strength import PasswordStrength
import itertools


class MasterDialogBase(Window):
    def __init__(self, parent, db, encryption):
        self.db = db
        self.encryption = encryption
        self.password_var = tk.StringVar()

        # noinspection PyProtectedMember
        assert self.encryption._db == self.db  # TODO: remove this when encryption/db is cleaned up

        super().__init__(parent, title="Master password")

    def _body(self, frame):
        self.resizable(False, False)
        self._error_label = ttk.Label(frame)
        self._error_label.grid(row=99)

    def _buttonbox(self):
        box = ttk.Frame(self)

        ttk.Frame(box).pack(side=tk.LEFT, fill=tk.X, expand=True)
        w = ttk.Button(box, text="OK", width=10, command=self.ok, default=tk.ACTIVE)
        w.pack(side=tk.LEFT, padx=2, pady=2)
        w = ttk.Button(box, text="Cancel", width=10, command=self.cancel)
        w.pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Frame(box).pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

        box.pack(fill=tk.BOTH, expand=True)

    def close(self):
        self.cancel()

    def ok(self, event=None):
        self.set_error_message('')
        if self.validate():
            self.withdraw()
            self.update_idletasks()
            self.apply()
            self.parent.focus_set()
            self.destroy()
        else:
            self.on_fail()
            self.initial_focus.focus()

    def validate(self):
        pass

    def apply(self):
        try:
            self.encryption.password = self.password_var.get()
            self.password_var.set('\0' * len(self.password_var.get()))
        except:
            messagebox.showerror(title="Failure", message=f"Failed to set master password. Operation aborted.")
            raise

    def set_error_message(self, message):
        self._error_label.configure(text=message)

    def on_fail(self):
        pass

    def cancel(self, event=None):
        pass


class MasterDialogCheck(MasterDialogBase):
    def __init__(self, parent, db, encryption):
        super().__init__(parent, db, encryption)

    def _body(self, frame):
        super()._body(frame)
        rowcount = itertools.count()
        ttk.Label(frame, text="Enter master password:").grid(row=next(rowcount))
        self.entry = PrivateEntry(frame, textvariable=self.password_var, width=38)
        self.entry.grid(row=next(rowcount))
        self.captcha = Captcha(frame)
        self.captcha.grid(row=next(rowcount))
        return self.entry

    def on_fail(self):
        super().on_fail()
        self.captcha.refresh()
        self.entry.delete(0, tk.END)

    def validate(self):
        if not self.captcha.validate():
            self.set_error_message("Invalid captcha!")
            return False
        elif not self.db.check_master_pwd(self.entry.get()):
            self.set_error_message("Invalid password!")
            return False
        return True

    def cancel(self, event=None):
        self.parent.destroy()


class MasterDialogInit(MasterDialogBase):
    def __init__(self, parent, db, encryption):
        super().__init__(parent, db, encryption)

    def _body(self, frame):
        super()._body(frame)
        rowcount = itertools.count()
        ttk.Label(frame, text="Set master password:").grid(row=next(rowcount))
        self.new_entry = PrivateEntry(frame, textvariable=self.password_var, width=38)
        self.new_entry.grid(row=next(rowcount))
        self.label = ttk.Label(frame)
        ttk.Label(frame, text="Confirm master password:").grid(row=next(rowcount))
        self.confirm_entry = PrivateEntry(frame, width=38)
        self.confirm_entry.grid(row=next(rowcount))
        PasswordStrength(frame, self.password_var).grid(row=next(rowcount))
        return self.new_entry

    def cancel(self, event=None):
        self.parent.destroy()

    def validate(self):
        if self.new_entry.get() != self.confirm_entry.get():
            self.set_error_message("Passwords don't match!")
            return False
        return True


class MasterDialogChange(MasterDialogBase):
    def __init__(self, parent, db, encryption):
        super().__init__(parent, db, encryption)

    def _body(self, frame):
        super()._body(frame)
        rowcount = itertools.count()
        ttk.Label(frame, text="Enter current master password:").grid(row=next(rowcount))
        self.old_entry = PrivateEntry(frame, width=38)
        self.old_entry.grid(row=next(rowcount))
        ttk.Label(frame, text="Set new master password:").grid(row=next(rowcount))
        self.new_entry = PrivateEntry(frame, textvariable=self.password_var, width=38)
        self.new_entry.grid(row=next(rowcount))
        self.label = ttk.Label(frame)
        ttk.Label(frame, text="Confirm master password:").grid(row=next(rowcount))
        self.confirm_entry = PrivateEntry(frame, width=38)
        self.confirm_entry.grid(row=next(rowcount))
        PasswordStrength(frame, self.password_var).grid(row=next(rowcount))
        return self.new_entry

    def cancel(self, event=None):
        self.parent.focus_set()
        self.destroy()

    def on_fail(self):
        super().on_fail()
        self.old_entry.delete(0, tk.END)

    def validate(self):
        if self.new_entry.get() != self.confirm_entry.get():
            self.set_error_message("Passwords don't match!")
            return False
        elif not self.db.check_master_pwd(self.old_entry.get()):
            self.set_error_message("Invalid password!")
            return False
        return True
