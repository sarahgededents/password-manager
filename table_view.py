import tkinter as tk

from context_menu import RightClickMenu
from data import FIELDS
from tkinter import ttk


class TableView(ttk.Treeview):
    COLUMNS = tuple(filter(lambda col: col != "#0", map(lambda field: field['tree_column'], FIELDS)))
    
    def match_search_string(search_string, row):
        search_tokens = search_string.split()
        token_matches = lambda token: any(map(lambda field: token in field, row))
        return all(map(lambda token: token_matches(token), search_tokens))

    def __init__(self, parent, db, func_decipher_private=None):
        super().__init__(parent, columns=TableView.COLUMNS)
        self.total_insert_call_count = 0
        self.insert_order = {}
        self.hidden = set()
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
        
    def delete(self, *items):
        for item in items:
            if item in self.hidden:
                self.hidden.remove(item)
        super().delete(*items)
    
    def show(self, item):
        if item in self.hidden:
            if self.exists(item):
                # these should be above us since they were added after and we only prepend
                visible_items_inserted_after = filter(lambda name: name not in self.hidden and self.insert_order[name] > self.insert_order[item], self.insert_order)
                next_neighbour = min(visible_items_inserted_after, default=None, key=lambda name: self.insert_order[name]) # should be right above us
                index = self.index(next_neighbour) + 1 if next_neighbour is not None else 0
                self.reattach(item, '', index)
                self.hidden.remove(item)
            else:
                raise ValueError("Something went wrong! Item was deleted from the table view but remains in self.hidden.")
    
    def hide(self, item):
        if item not in self.hidden and self.exists(item):
            self.hidden.add(item)
            self.detach(item)
            
    def set_visible(self, item, visible):
        if visible:
            self.show(item)
        else:
            self.hide(item)
            
    def filter_by_search_string(self, search_string):
        all_rows = self.get_children() + tuple(self.hidden)
        is_visible = lambda row: TableView.match_search_string(search_string, row)
        for name in all_rows:
            row = (name,) + self.item(name, option='values')
            self.set_visible(name, is_visible(row))
        
    def selection_clear(self):
        for item in self.selection():
            self.selection_remove(item)
        
    def delete_selection(self, event):
        name = self.get_selected_name()
        if name is not None:
            self.db.delete(name)    
    
    def get_selected_name(self):
        selection = self.selection()
        return selection[0] if selection else None
    
    def insert(self, parent, index, iid, *args, **kwargs):
        super().insert(parent, index, iid, *args, **kwargs)
        self.insert_order[iid] = self.total_insert_call_count
        self.total_insert_call_count += 1
    
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