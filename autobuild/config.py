import os, sys

class Config:

    def __init__(self, stem = None, path = None, load = True):
    
        if path is not None:
            self.path = path
        else:
            if stem is None:
                name = os.path.split(sys.argv[0])[1]
                stem = os.path.splitext(name)[0]
            
            home_dir = os.getenv("HOME", os.path.split(os.path.abspath(__file__))[0])
            self.path = os.path.join(home_dir, "." + stem)
        
        if load:
            self.load()
    
    def lock(self, f):

        fcntl.flock(f, fcntl.LOCK_EX)

    def unlock(self, f):

        fcntl.flock(f, fcntl.LOCK_UN)

    def load(self):
    
        try:
            f = open(self.path)
            self.lock(f)
            self._load(f)
            self.unlock(f)
            f.close()
        
        except IOError:
            self.lines = {}
    
    def _load(self, f):
    
        self.lines = {}
        
        for line in f.readlines():
        
            at = line.find(": ")
            label, values = line[:at], line[at + 2:].rstrip().split("\t")
            self.lines[label] = values
    
    def save(self):
    
        try:
            f = open(self.path, "w")
            self.lock(f)
            self._save(f)
            self.unlock(f)
            f.close()
        
        except IOError:
            sys.stderr.write("Failed to update the configuration file.\n")
    
    def _save(self, f):

        items = self.lines.items()
        items.sort()
        for label, values in items:
            f.write(label + ": " + "\t".join(values) + "\n")

    def check(self, label, value):
    
        if label in self.lines:
            return True
        
        return value in self.lines.values()
    
    def check_label(self, label):
    
        return label in self.lines
    
    def add(self, label, value):
    
        self.lines[label] = value
    
    def remove(self, label):

        del self.lines[label]

