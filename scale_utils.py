class TraceWriteCallbackOnChanged:
    def __init__(self, var, cmd):
        self.var = var
        self.cache = var.get()
        self.cmd = cmd
        var.trace('w', self)
        
    def __call__(self, *args):
        data = self.var.get()
        if data != self.cache:
            self.cache = data
            self.cmd(*args)
            
def ttk_scale_int(intvar):
    return lambda s: intvar.set(int(float(s)))