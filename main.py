import tkinter as tk
from tkinter import ttk
from pwd_save import generate_password
from collections import namedtuple
from interface import submit, delete, update

class PasswordGeneratorWidget(tk.Frame):
    def __init__(self, root, password_var):
        super().__init__(root)
        self.password_var = password_var
        self.length_var = tk.IntVar(self, value=8)
        self.regen_btn = tk.Button(self, text = "Generate password", command=self.on_generate_password)
        self.slider = tk.Scale(self, variable=self.length_var, from_=1, to=35, sliderrelief=tk.FLAT, orient=tk.HORIZONTAL, command=lambda x: self.on_generate_password())
        self.slider.pack()
        self.regen_btn.pack()

    def on_generate_password(self):
        password = generate_password(self.length_var.get())
        self.password_var.set(password)
        
class Form(tk.Frame):
    class Field:
        def __init__(self, root, uid, name, private=False, **kwargs):
            show = "*" if private else None # TODO: should be checkboxable
            self.uid = uid
            self.var = tk.StringVar()
            self.label = tk.Label(root, text = name)
            self.entry = tk.Entry(root, width=30, textvariable=self.var, show=show)
    
    def __init__(self, root, field_descriptors, on_submit=lambda form:None, on_update=lambda form:None, on_delete=lambda name:None):
        super().__init__(root)
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
        self.update_btn.grid(row=self.rowcount, column=1)
        self.submit_btn.grid(row=self.rowcount, column=1, columnspan=2)
        self.delete_btn.grid(row=self.rowcount, column=2)
            
    def add_field(self, field_descriptor):
        field = Form.Field(self, **field_descriptor)
        self.fields[field.uid] = field
        field.label.grid(row=self.rowcount, column=0)
        field.entry.grid(row=self.rowcount, column=1, columnspan=2)
        self.rowcount += 1
        setattr(self, field.uid, field.var) # easier access to each var from outside
        
    def _get_fields_as_namedtuple(self):
        values = [f.var.get() for f in self.fields.values()]
        return namedtuple("Form", self.fields.keys())(*values)
    
    def on_submit_click(self):
        fields = self._get_fields_as_namedtuple()
        self.on_submit_callback(fields)
        
    def on_update_click(self):
        fields = self._get_fields_as_namedtuple()
        self.on_update_callback(fields)
    
    def on_delete_click(self):
        self.on_delete_callback(self.name.get())
                


FIELDS = [
    {'uid': 'name', 'name': 'Name', 'tree_column': '#0'},
    {'uid': 'email', 'name': 'Email'},
    {'uid': 'password', 'name': 'Password', 'private': True},
    {'uid': 'website', 'name': 'Website'}
]
for field in FIELDS:
    field['tree_column'] = field.get('tree_column', field['uid']) 

i=0 # temporary serial id count until sqlite takes care of it cleanly
def make_tree_view(root):
    tree = ttk.Treeview(root)
    tree["columns"] = tuple(filter(lambda col: col != "#0", map(lambda field: field['tree_column'], FIELDS)))
    for field in FIELDS:
        tree.heading(field['tree_column'], text=field['name'])
    return tree

def fill_layout(root):
    top = tk.Frame(root)
    bottom = tk.Frame(root)
    treeview = make_tree_view(bottom)
    def insert(f):
        print(f) #TODO sql query here instead, also encrypt password maybe?
        submitted, err = submit(f)
        if submitted:
            global i
            password = '*' * len(f.password)
            treeview.insert("", "end", i, text=f.name, values=(f.email, password, f.website))
            i += 1
        else:
            print(err)
    
    form = Form(top, FIELDS, on_submit=insert, on_update=update, on_delete=delete)
    pgw = PasswordGeneratorWidget(top, form.password)

    top.pack(side=tk.TOP)
    form.pack(side=tk.LEFT)
    pgw.pack(side=tk.LEFT)
    bottom.pack(fill=tk.Y)
    treeview.pack(fill=tk.BOTH)

def make_root_window(width=600, height=400):
    root = tk.Tk()
    root.title("Password Manager")
    root.iconbitmap(default='pwd.ico')
    return root

def main():
    root = make_root_window()
    fill_layout(root)
    root.mainloop()

if __name__ == '__main__':
    main()
