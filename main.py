import tkinter as tk
from tkinter import ttk
from pwd_save import generate_password, Encryption
from collections import namedtuple
from interface import DatabaseManager

class PasswordGeneratorWidget(tk.Frame):
    def __init__(self, root, password_var):
        super().__init__(root)
        self.password_var = password_var
        self.length_var = tk.IntVar(self, value=8)
        self.regen_btn = tk.Button(self, text = "Generate password", command=self.on_generate_password)
        self.slider = tk.Scale(self, variable=self.length_var, from_=1, to=32, sliderrelief=tk.FLAT, orient=tk.HORIZONTAL, command=lambda x: self.on_generate_password())
        self.slider.pack()
        self.regen_btn.pack()

    def on_generate_password(self):
        password = generate_password(self.length_var.get())
        self.password_var.set(password)

class PrivateEntry(tk.Frame):
    def __init__(self, master, width=20, **kwargs):
        super().__init__(master)
        self.is_showing_stars = tk.BooleanVar(self, value=True)
        self.entry = tk.Entry(self, width=width-3, **kwargs)
        self.checkbox = tk.Checkbutton(self, onvalue=False, offvalue=True, variable=self.is_showing_stars)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.checkbox.pack(side=tk.RIGHT)
        self._update_show_stars()
        self.is_showing_stars.trace('w', self._update_show_stars)
        
    def bind(self, *args, **kwargs):
        return self.entry.bind(*args, **kwargs)
        
    def get(self, *args, **kwargs):
        return self.entry.get(*args, **kwargs)
        
    def delete(self, *args, **kwargs):
        return self.entry.delete(*args, **kwargs)
    
    def _update_show_stars(self, *args):
        show = "*" if self.is_showing_stars.get() else ""
        self.entry.config(show=show)

class Form(tk.Frame):
    class Field:
        def __init__(self, form, uid, name, private=False, **kwargs):
            self.private = private
            self.form = form
            self.uid = uid
            self.var = tk.StringVar()
            self.label = tk.Label(form, text = name)
            entryType = PrivateEntry if self.private else tk.Entry
            self.entry = entryType(form, width=38, textvariable=self.var)
            self.entry.bind("<Return>", self.on_return_pressed)
            #self.entry.bind("<Escape>", self.clear)
        
        def clear(self, event=None):
            self.var.set("")
            
        def on_return_pressed(self, event=None):
            self.form.on_return_pressed(event)
    
    def __init__(self, root, field_descriptors, db, encryption, on_submit=lambda form:None, on_update=lambda form:None, on_delete=lambda name:None):
        super().__init__(root)
        self.db = db
        self.encryption = encryption
        self.rowcount = 0
        self.fields = {}
        for field_desc in field_descriptors:
            self.add_field(field_desc)
        self.submit_btn = tk.Button(self, text="Submit", command=self.on_submit_click)
        self.update_btn = tk.Button(self, text="Update", command=self.on_update_click)
        self.delete_btn = tk.Button(self, text="Delete", command=self.on_delete_click)
        self.on_submit_callback = on_submit
        self.on_update_callback = on_update
        self.on_delete_callback = on_delete
        self.update_btn_visibility()
        self.name.trace('w', self.update_btn_visibility)
        self.password.trace('w', self._limit_max_pwd_length)
        

        
    def add_field(self, field_descriptor):
        field = Form.Field(self, **field_descriptor)
        self.fields[field.uid] = field
        field.label.grid(row=self.rowcount, column=0)
        field.entry.grid(row=self.rowcount, column=1, columnspan=2, sticky=tk.W)
        self.rowcount += 1
        setattr(self, field.uid, field.var) # easier access to each var from outside
    
    def clear(self):
        for f in self.fields:
            f.clear()
    
    def load(self, name):
        if name is None:
            self.clear()
        else:
            row = self.db.fetch_one(name)
            self.name.set(row.name)
            self.email.set(row.email)
            self.password.set(self.encryption.decrypt(row.password))
            self.website.set(row.website)
        
    def on_submit_click(self):
        fields = self._get_fields_as_namedtuple()
        self.on_submit_callback(fields)
        
    def on_update_click(self):
        fields = self._get_fields_as_namedtuple()
        self.on_update_callback(fields)
    
    def on_delete_click(self):
        self.on_delete_callback(self.name.get())
        
    def on_return_pressed(self, event=None):
        if self.db.exists(self.name.get()):
            self.on_update_click()
        else:
            self.on_submit_click()

    def _get_fields_as_namedtuple(self):
        values = [f.var.get() for f in self.fields.values()]
        ntuple = namedtuple("Form", self.fields.keys())(*values)
        ntuple = ntuple._replace(password=self.encryption.encrypt(ntuple.password)) #to encrypt password as soon as possible
        return ntuple

    def update_btn_visibility(self, *args):
        if self.db.exists(self.name.get()):
            self.submit_btn.grid_forget()
            self.update_btn.grid(row=self.rowcount, column=1)
            self.delete_btn.grid(row=self.rowcount, column=2)
        else:
            self.submit_btn.grid(row=self.rowcount, column=1, columnspan=2)
            self.update_btn.grid_forget()
            self.delete_btn.grid_forget()
    
    def _limit_max_pwd_length(self, *args):
        if len(self.password.get()):
            self.password.set(self.password.get()[:32])
    
            
class MasterDialog(tk.simpledialog.Dialog):
    class Mode:
        CHECK = 0
        SET = 1
    
    def __init__(self, parent, db, encryption=None, mode=Mode.CHECK):
        self.db = db
        self.encryption = encryption
        self.mode = mode if self.db.has_master_pwd() else MasterDialog.Mode.SET
        super().__init__(parent, title="Master password")

    def body(self, master):
        verb = self._get_verb()
        tk.Label(master, text=f"{verb} master password:").grid(row=0)
        self.entry = PrivateEntry(master, width=38)
        self.entry.grid(row=1)
        if self.mode == MasterDialog.Mode.SET:
            tk.Label(master, text="Confirm master password:").grid(row=2)
            self.entry2 = PrivateEntry(master, width=38)
            self.entry2.grid(row=3)
        self.label = tk.Label(master)     
        return self.entry
    
    def ok(self, event=None):
        if not self.validate():
            self.initial_focus.focus_set()
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
            self.db.set_master_pwd(self.entry.get())
        if self.encryption is not None:
            self.encryption.key = self.entry.get()
    
    def validate(self):
        if self.mode == MasterDialog.Mode.CHECK:
            if not self.db.check_master_pwd(self.entry.get()):
                self.initial_focus.focus_set()
                self.label.configure(text="Invalid password!")
                self.label.grid(row=2)
                self.entry.delete(0, tk.END)
                return False
        elif self.mode == MasterDialog.Mode.SET:
            if self.entry.get() != self.entry2.get():
                self.label.configure(text="Passwords don't match!")
                self.label.grid(row=4)
                return False
        return True

    def _is_changing_password(self):
        return self.mode == MasterDialog.Mode.SET and self.db.has_master_pwd()
    
    def _get_verb(self):
        if self.mode == MasterDialog.Mode.CHECK:
            return "Enter"
        elif self.mode == MasterDialog.Mode.SET:
            return "Set new" if self._is_changing_password() else "Set"
        return "Enter"

FIELDS = [
    {'uid': 'name', 'name': 'Name', 'tree_column': '#0'},
    {'uid': 'email', 'name': 'Email'},
    {'uid': 'password', 'name': 'Password', 'private': True},
    {'uid': 'website', 'name': 'Website'}
]
for field in FIELDS:
    field['tree_column'] = field.get('tree_column', field['uid']) 

def make_tree_view(root):
    tree = ttk.Treeview(root, columns = tuple(filter(lambda col: col != "#0", map(lambda field: field['tree_column'], FIELDS))))
    for field in FIELDS:
        tree.column(field['tree_column'], anchor=tk.CENTER, minwidth=50, width=0, stretch=tk.YES)
        tree.heading(field['tree_column'], text=field['name'])
    return tree

def fill_layout(root, db, encryption):
    top = tk.Frame(root)
    bottom = tk.Frame(root)
    treeview = make_tree_view(bottom)
    tools_panel = tk.Frame(top)
    form = Form(top, FIELDS, db, encryption, on_submit=db.submit, on_update=db.update, on_delete=db.delete)
    pgw = PasswordGeneratorWidget(tools_panel, form.password)
    change_master_btn = tk.Button(tools_panel, text="Change master password", command=lambda: MasterDialog(root, db, encryption, MasterDialog.Mode.SET))

    top.pack(side=tk.TOP)
    form.pack(side=tk.LEFT)
    tools_panel.pack(side=tk.LEFT)
    change_master_btn.pack()
    pgw.pack()
    bottom.pack(fill=tk.BOTH, expand=True)
    treeview.pack(fill=tk.BOTH, expand=True)
    
    def set_values(event):
        name = treeview.selection()[0] if treeview.selection() else None
        form.load(name)
    
    def del_selected(event):
        name = treeview.selection()[0] if treeview.selection() else None
        if name is not None:
            db.delete(name)

    treeview.bind("<Delete>", del_selected)
    treeview.bind("<<TreeviewSelect>>", set_values)
    
    def on_submit(f):
        treeview.insert("", 0, f.name, text=f.name, values=fields_to_values(f))
        treeview.focus(f.name)
        treeview.selection_set(f.name)
        form.update_btn_visibility()
        
    def on_delete(name):
        treeview.delete(name)
        form.update_btn_visibility()

    fields_to_values = lambda f: (f.email, '*' * 8, f.website)
    db.on_submit = on_submit
    db.on_delete = on_delete
    db.on_update = lambda f: treeview.item(f.name, values=fields_to_values(f))
    
    rows = db.fetch_all()
    for fields in rows:
        treeview.insert("", 0, fields.name, text=fields.name, values=fields_to_values(fields))

def make_root_window(width=500, height=700):
    root = tk.Tk()
    root.title("Password Manager")
    root.geometry(f'{width}x{height}')
    root.minsize(420, 300)
    root.iconbitmap(default='pwd.ico')
    return root

def main():
    db = DatabaseManager("passmanager.db")
    root = make_root_window()
    encryption = Encryption()
    fill_layout(root, db, encryption)
    MasterDialog(root, db, encryption)
    root.mainloop()

if __name__ == '__main__':
    main()
