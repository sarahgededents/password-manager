import tkinter as tk
import tkinter.simpledialog
from tkinter import ttk
from pwd_save import generate_password, Encryption
from collections import namedtuple
from interface import DatabaseManager
import center_tk_window
import webbrowser


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
        self.entry = ClipboardEntry(self, width=width-3, **kwargs)
        self.checkbox = tk.Checkbutton(self, onvalue=False, offvalue=True, variable=self.is_showing_stars)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.checkbox.pack(side=tk.RIGHT)
        self._update_show_stars()
        self.is_showing_stars.trace('w', self._update_show_stars)
        
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
        
        
class ClipboardEntry(tk.Entry):
    def __init__(self, parent, *args, **kwargs):
        tk.Entry.__init__(self, parent, *args, **kwargs)
        
        self.changes = [""]
        self.steps = int()
        
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Cut")
        self.context_menu.add_command(label="Copy")
        self.context_menu.add_command(label="Paste")
        
        self.bind("<Button-3>", self.popup)
        self.bind("<Control-z>", self.undo)
        self.bind("<Control-y>", self.redo)
        self.bind("<Key>", self.add_changes)
        
    def add_changes(self, event=None):
        if self.get() != self.changes[-1]:
            self.changes.append(self.get())
            self.steps += 1
        
        
    def popup(self, event):
        self.context_menu.post(event.x_root, event.y_root)
        self.context_menu.entryconfigure("Cut", command=lambda: self.event_generate("<<Cut>>"))
        self.context_menu.entryconfigure("Copy", command=lambda: self.event_generate("<<Copy>>"))
        self.context_menu.entryconfigure("Paste", command=lambda: self.event_generate("<<Paste>>"))

    def undo(self, event=None):
        if self.steps != 0:
            self.steps -= 1
            self.delete(0, tk.END)
            self.insert(tk.END, self.changes[self.steps])

    def redo(self, event=None):
        if self.steps < len(self.changes):
            self.delete(0, tk.END)
            self.insert(tk.END, self.changes[self.steps])
            self.steps += 1


class Form(tk.Frame):
    class Field:
        def __init__(self, form, uid, name, private=False, **kwargs):
            self.private = private
            self.form = form
            self.uid = uid
            self.var = tk.StringVar()
            self.label = tk.Label(form, text = name)
            entryType = PrivateEntry if self.private else ClipboardEntry
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
        
        db.on_submit.append( self.update_btn_visibility )
        db.on_delete.append( self.update_btn_visibility )
        
        
    def add_field(self, field_descriptor):
        field = Form.Field(self, **field_descriptor)
        self.fields[field.uid] = field
        field.label.grid(row=self.rowcount, column=0)
        field.entry.grid(row=self.rowcount, column=1, columnspan=2, sticky=tk.W)
        self.rowcount += 1
        setattr(self, field.uid, field.var) # easier access to each var from outside
    
    def clear(self):
        for f in self.fields.values():
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
        result = self.on_submit_callback(fields)
        self._handle_error(result, title="Submit error")
        
    def on_update_click(self):
        if tk.messagebox.askyesno("Update", "Are you sure ?"):
            fields = self._get_fields_as_namedtuple()
            result = self.on_update_callback(fields)
            self._handle_error(result, title="Update error")
    
    def on_delete_click(self):
        if tk.messagebox.askyesno("Delete", "Are you sure ?"):
            result = self.on_delete_callback(self.name.get())
            if result:
                self.clear()
            else:
                self._handle_error(result, title="Delete error")
            
        
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
    
    def _handle_error(self, result, title):
        message = getattr(result, "message", None)
        if not result and message is not None:
            tk.messagebox.showwarning(title=title, message=message)

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
            self.db.set_master_pwd(self.entry.get())
        if self.encryption is not None:
            self.encryption.key = self.entry.get()
    
    def validate(self):
        if self.mode == MasterDialog.Mode.CHECK:           
            if not self.db.check_master_pwd(self.entry.get()):
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
    {'uid': 'name', 'name': 'Name', 'tree_column': '#0', 'can_copy': True},
    {'uid': 'email', 'name': 'Email', 'can_copy': True},
    {'uid': 'password', 'name': 'Password', 'private': True, 'can_copy': True},
    {'uid': 'website', 'name': 'Website', 'can_copy': True, 'can_goto': True}
]
for field in FIELDS:
    field['tree_column'] = field.get('tree_column', field['uid'])


class RightClickMenu(tk.Menu):
    def __init__(self, parent, db, func_decipher_private=None):
        super().__init__(parent, tearoff=0)
        self.db = db
        self.func_decipher_private = func_decipher_private
        for f in FIELDS:
            is_decipherable = not f.get('private', False) or callable(func_decipher_private)

            if f.get('can_copy', False) and is_decipherable:
                name = f['name']
                print(f)
                self.add_command(label=f"Copy {name}", command=lambda f=f: self.copy_field(f))
        self.add_separator()
        for f in FIELDS:
            is_decipherable = not f.get('private', False) or callable(func_decipher_private)
            if f.get('can_goto', False) and is_decipherable:
                name, cmd = f['name'], lambda: self.goto_field(f)
                self.add_command(label=f"Go to {name}", command=cmd)
        self.add_separator()
        self.add_command(label="Delete", command=self.delete)
    
    def copy_field(self, field_desc):
        #print(field_desc)
        field_value = self._get_field_value(field_desc)
        if field_value is not None:
            copy_to_clipboard(self, field_value)
        else:
            tk.simpledialog.showerror("Something went wrong!")
        
    def goto_field(self, field_desc):
        field_value = self._get_field_value(field_desc)
        if field_value is not None:
            webbrowser.open_new(field_value)
        else:
            tk.simpledialog.showerror("Something went wrong!")
    
    def _get_field_value(self, field_desc):
        fields = getattr(self, 'fields', None)
        if fields is not None:
            field_value = getattr(fields, field_desc['uid'])
            if field_desc.get('private', False):
                field_value = self.func_decipher_private(field_value)
            return field_value
    
    def delete(self):
        if self.fields is not None:
            if tk.messagebox.askyesno("You sure?"):
                self.db.delete(self.fields.name)
        else:
            tk.simpledialog.showerror("Something went wrong!")

class TableView(ttk.Treeview):
    COLUMNS = tuple(filter(lambda col: col != "#0", map(lambda field: field['tree_column'], FIELDS)))

    def __init__(self, parent, db, func_decipher_private=None):
        super().__init__(parent, columns=TableView.COLUMNS)
        self.db = db
        for field in FIELDS:
            self.column(field['tree_column'], anchor=tk.CENTER, minwidth=50, width=0, stretch=tk.YES)
            self.heading(field['tree_column'], text=field['name'])
        for fields in db.fetch_all():
            self.insert("", 0, fields.name, text=fields.name, values=self._fields_to_values(fields))
        self.context_menu = RightClickMenu(self, db, func_decipher_private)

        self.bind("<Button-3>", self.show_context_menu)
        self.bind("<Delete>", self.delete_selection)
        db.on_submit.append( self.prepend )
        db.on_delete.append( self.delete )
        db.on_update.append( self.update_fields )
        
    def delete_selection(self, event):
        name = self.get_selected_name()
        if name is not None:
            self.db.delete(name)    
    
    def get_selected_name(self):
        selection = self.selection()
        return selection[0] if selection else None
    
    def prepend(self, fields):
        self.insert("", 0, fields.name, text=fields.name, values=self._fields_to_values(fields))
        self.focus(fields.name)
        self.selection_set(fields.name)
        
    def update_fields(self, fields):
        self.item(fields.name, values=self._fields_to_values(fields))
        
    def show_context_menu(self, event):
        iid = self.identify_row(event.y)
        if iid:
            self.selection_set(iid)
            self.context_menu.fields = self.db.fetch_one(iid)
            if self.context_menu.fields is not None:
                self.context_menu.post(event.x_root, event.y_root)
        else:
            self.context_menu.fields = None
        
    def _fields_to_values(self, fields):
        return (fields.email, '*' * 8, fields.website)
            

def fill_layout(root, db, encryption):
    top = tk.Frame(root)
    top.pack(side=tk.TOP)
    
    form = Form(top, FIELDS, db, encryption, on_submit=db.submit, on_update=db.update, on_delete=db.delete)
    form.pack(side=tk.LEFT)
    
    tools_panel = tk.Frame(top)
    tools_panel.pack(side=tk.LEFT)
    change_master_btn = tk.Button(tools_panel, text="Change master password", command=lambda: MasterDialog(root, db, encryption, MasterDialog.Mode.SET))
    change_master_btn.pack()
    pgw = PasswordGeneratorWidget(tools_panel, form.password)
    pgw.pack()
    
    bottom = tk.Frame(root)
    bottom.pack(fill=tk.BOTH, expand=True)
    
    table = TableView(bottom, db)
    table.bind("<<TreeviewSelect>>", lambda event: form.load(table.get_selected_name()))
    table.pack(fill=tk.BOTH, expand=True)

def copy_to_clipboard(root, text):
    root.clipboard_clear()
    root.clipboard_append(text)

def make_root_window(width=500, height=700):
    root = tk.Tk()
    root.title("Password Manager")
    root.geometry(f'{width}x{height}')
    root.minsize(420, 300)
    return root



def main():
    db = DatabaseManager("passmanager.db")
    root = make_root_window()
    
    center_tk_window.center_on_screen(root)
    
    encryption = Encryption()
    fill_layout(root, db, encryption)
    
    MasterDialog(root, db, encryption)
    

    root.mainloop()

if __name__ == '__main__':
    main()
