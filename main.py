import center_tk_window
import tkinter as tk
import tkinter.simpledialog
from tkinter import messagebox

from data import FIELDS
from database import DatabaseManager
from encryption import Encryption
from entry import NamedEntry
from form import Form
from functools import partial
from generate_password import GeneratePassword
from master_dialog import MasterDialogInit, MasterDialogChange, MasterDialogCheck
from table_view import TableView
from tkinter import ttk
from ttkthemes import ThemedTk


def fill_layout(root, db, encryption):
    top = ttk.Frame(root)
    top.pack(side=tk.TOP, fill=tk.X)
    
    ttk.Frame(top).pack(side=tk.LEFT, fill=tk.X, expand=True) #hfill
    form = Form(top, FIELDS, db, encryption, on_submit=db.submit, on_update=db.update, on_delete=db.delete)
    form.pack(side=tk.LEFT)
    tools_panel = ttk.Frame(top)
    tools_panel.pack(side=tk.LEFT)
    ttk.Frame(top).pack(side=tk.LEFT, fill=tk.X, expand=True) #hfill
    
    change_master_btn = ttk.Button(tools_panel, text="Change master password", command=lambda: MasterDialogChange(root, db, encryption))
    change_master_btn.pack()
    def show_generate_pwd_dialog():
        pwd = GeneratePassword.show_dialog(root)
        if pwd is not None:
            form.password.set(pwd)
    ttk.Button(tools_panel, text="Generate password", command=show_generate_pwd_dialog).pack()
    
    bottom = ttk.Frame(root)
    bottom.pack(fill=tk.BOTH, expand=True)

    show_error = partial(messagebox.showerror, "Decryption failure")
    decrypt = partial(encryption.decrypt, report_error_func=show_error)
    table = TableView(bottom, db, decrypt, on_select=form.load)
    
    searchvar = tk.StringVar()
    searchvar.trace('w', lambda *args: table.filter_by_search_string(searchvar.get()))
    NamedEntry(bottom, 'Search', width=61, textvariable=searchvar).pack()
    table.pack(fill=tk.BOTH, expand=True)
    
    
    def clear_all():
        form.clear()
        table.selection_clear()
    ttk.Button(tools_panel, text="Clear form and selection", command=clear_all).pack()



def make_root_window(width=500, height=700):
    root = ThemedTk(theme="arc")
    root.title("Password Manager")
    root.geometry(f'{width}x{height}')
    root.minsize(480, 300)
    return root


def main():
    db = DatabaseManager("passmanager.db")
    root = make_root_window()
    
    center_tk_window.center_on_screen(root)
    
    encryption = Encryption(db)
    fill_layout(root, db, encryption)

    if db.has_master_pwd():
        MasterDialogCheck(root, db, encryption)
    else:
        MasterDialogInit(root, db, encryption)

    root.mainloop()

if __name__ == '__main__':
    main()
