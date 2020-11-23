import tkinter as tk
import webbrowser

from data import FIELDS

def copy_to_clipboard(root, text):
    root.clipboard_clear()
    root.clipboard_append(text)

class RightClickMenu(tk.Menu):
    def __init__(self, parent, db, func_decipher_private=None):
        super().__init__(parent, tearoff=0)
        self.db = db
        self.func_decipher_private = func_decipher_private
        for f in FIELDS:
            is_decipherable = not f.get('private', False) or callable(func_decipher_private)

            if f.get('can_copy', False) and is_decipherable:
                name = f['name']
                self.add_command(label=f"Copy {name}", command=lambda f=f: self.copy_field(f))
        self.add_separator()
        for f in FIELDS:
            is_decipherable = not f.get('private', False) or callable(func_decipher_private)
            if f.get('can_goto', False) and is_decipherable:
                name, cmd = f['name'], lambda f=f: self.goto_field(f)
                self.add_command(label=f"Go to {name}", command=cmd)
        self.add_separator()
        self.add_command(label="Delete", command=self.delete)
    
    def copy_field(self, field_desc):
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