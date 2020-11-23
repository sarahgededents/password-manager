import tkinter as tk

from captcha.image import ImageCaptcha
from ui.entry import ClipboardEntry
from PIL import ImageTk
from security.utils import generate_captcha_string
from tkinter import ttk

class Captcha(ttk.Frame):
    def __init__(self, parent):
        self.captcha = ImageCaptcha()
        super().__init__(parent)
        self.label = ttk.Label(self)
        self.entry = ClipboardEntry(self, width=10)
        self.label.grid(row=0, column=0, columnspan=1)
        self.entry.grid(row=1, column=0, columnspan=2)
        
        ttk.Button(self, text="refresh", command=self.refresh).grid(row=0, column=5, columnspan=1)
        
        self.refresh()
    
    def refresh(self):
        self.result = generate_captcha_string()
        image = self.captcha.generate_image(self.result)
        self.image = ImageTk.PhotoImage(image)
        self.label.configure(image=self.image)
        self.entry.delete(0, tk.END)
    
    def validate(self):
        result = self.result == self.entry.get()
        self.entry.delete(0, tk.END)
        return result