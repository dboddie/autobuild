import lockfile, os, sys

class Config:

    def __init__(self, stem = None):
    
        if stem is None:
            name = os.path.split(sys.argv[0])[1]
            stem = os.path.splitext(name)[0]
        
        home_dir = os.getenv("HOME", os.path.split(os.path.abspath(__file__))[0])
        self.path = os.path.join(home_dir, "." + stem)
        self.load()
    
    def load(self):
    
        try:
            self.lines = {}
            lock = lockfile.FileLock(self.path)
            lock.acquire()

            f = open(self.path)

            for line in f.readlines():
            
                at = line.find(": ")
                label, values = line[:at], line[at + 2:].rstrip().split("\t")
                self.lines[label] = values
            
            f.close()
            lock.release()
        
        except IOError:
            self.lines = {}
    
    def save(self):
    
        try:
            lock = lockfile.FileLock(self.path)
            lock.acquire()

            f = open(self.path, "w")

            items = self.lines.items()
            items.sort()
            for label, values in items:
                f.write(label + ": " + "\t".join(values) + "\n")

            f.close()
            lock.release()
        
        except IOError:
            sys.stderr.write("Failed to update the configuration file.\n")
    
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

