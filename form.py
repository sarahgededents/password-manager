import tkinter as tk

from collections import namedtuple
from entry import ClipboardEntry
from generate_password import ARE_YOU_SURE_MSG, confirm_once, confirm_weak_password
from private_entry import PrivateEntry
from tkinter import ttk

class Form(ttk.Frame):
    class Field:
        def __init__(self, parent, uid, name, private=False, form=None, **kwargs):
            self.private = private
            self.form = form if form is not None else parent
            self.uid = uid
            self.var = tk.StringVar()
            self.label = ttk.Label(parent, text = name)
            entryType = PrivateEntry if self.private else ClipboardEntry
            self.entry = entryType(parent, width=38, textvariable=self.var)
            self.entry.bind("<Return>", self.on_return_pressed)
            #self.entry.bind("<Escape>", self.clear)
        
        def clear(self, event=None):
            self.var.set("")
            self.entry.clear_history()
            
        def on_return_pressed(self, event=None):
            self.form.on_return_pressed(event)
        
    
    def __init__(self, root, field_descriptors, db, encryption, on_submit=lambda form:None, on_update=lambda form:None, on_delete=lambda name:None):
        super().__init__(root)
        self.db = db
        self.encryption = encryption
        self.rowcount = 0
        self.fields = {}
        
        self.entry_frame = ttk.Frame(self)
        self.entry_frame.grid(row = 0, column = 0, columnspan = 4)
        
        for field_desc in field_descriptors:
            self.add_field(field_desc)
        self.submit_btn = ttk.Button(self, text="Submit", command=self.on_submit_click)
        self.update_btn = ttk.Button(self, text="Update", command=self.on_update_click)
        self.delete_btn = ttk.Button(self, text="Delete", command=self.on_delete_click)
        
        self.on_submit_callback = on_submit
        self.on_update_callback = on_update
        self.on_delete_callback = on_delete
        self.update_btn_visibility()
        self.name.trace('w', self.update_btn_visibility)
        self.password.trace('w', self._limit_max_pwd_length)
        
        db.on_submit.append( self.update_btn_visibility )
        db.on_delete.append( self.update_btn_visibility )
        
        
    def add_field(self, field_descriptor):
        field = Form.Field(self.entry_frame, form=self, **field_descriptor)
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
        if confirm_weak_password(self.password.get()):
            fields = self._get_fields_as_namedtuple()
            result = self.on_submit_callback(fields)
            self._handle_error(result, title="Submit error")
        
    def on_update_click(self):
        if confirm_once("Update", self.password.get()):
            fields = self._get_fields_as_namedtuple()
            result = self.on_update_callback(fields)
            self._handle_error(result, title="Update error")
            
    
    def on_delete_click(self):
        if tk.messagebox.askyesno("Delete", ARE_YOU_SURE_MSG):
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
            self.delete_btn.grid(row=self.rowcount, column=3)
        else:
            self.submit_btn.grid(row=self.rowcount, column=2)
            self.update_btn.grid_forget()
            self.delete_btn.grid_forget()
    
    def _limit_max_pwd_length(self, *args):
        if len(self.password.get()):
            self.password.set(self.password.get()[:32])