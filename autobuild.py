#!/usr/bin/env python

import commands, os, sys, tempfile

def mkdir(path):

    if os.path.isdir(path):
        print "Directory", path, "already exists."
        return
    
    try:
        os.mkdir(path)
        print "Created", path
    except OSError:
        sys.stderr.write("Failed to create directory: %s\n" % path)
        sys.exit(1)

def rmdir(path):

    try:
        os.rmdir(path)
        print "Removed", path
    except OSError:
        sys.stderr.write("Failed to remove directory: %s\n" % path)
        sys.exit(1)

def remove_dir(path):

    if os.system("sudo rm -rf " + commands.mkarg(path)) == 0:
        print "Removed", path, "and its contents."
        return True
    else:
        sys.stderr.write("Failed to remove directory: %s\n" % path)
        return False

def write_file(path, text):

    try:
        open(path, "w").write(text)
        print "Created", path
    except IOError:
        sys.stderr.write("Failed to write file: %s\n" % path)
        sys.exit(1)

class Config:

    def __init__(self):
    
        this_dir = os.path.split(os.path.abspath(__file__))[0]
        self.path = os.path.join(this_dir, "active")
        self.load()
    
    def load(self):
    
        try:
            self.lines = {}
            for line in open(self.path).readlines():
            
                at = line.find(": ")
                label, values = line[:at], line[at + 2:].rstrip().split("\t")
                self.lines[label] = values
        
        except IOError:
            self.lines = {}
    
    def save(self):
    
        try:
            f = open(self.path, "w")
            items = self.lines.items()
            items.sort()
            for label, values in items:
                f.write(label + ": " + "\t".join(values) + "\n")
            f.close()
        
        except IOError:
            sys.stderr.write("Failed to update the list of active chroots.\n")
    
    def make_line(self, *args):
    
        return " ".join(args)
    
    def check(self, label, template, install_dir, distribution, pbuilderrc):
    
        if label in self.lines:
            return True
        
        new_line = self.make_line(template, install_dir, distribution, pbuilderrc)
        
        return line in self.lines.values()
    
    def check_label(self, label):
    
        if not label in self.lines:
        
            sys.stderr.write("No chroot exists with that configuration.\n")
            sys.exit(1)
    
    def add(self, label, template, install_dir, distribution, pbuilderrc):
    
        new_line = self.make_line(template, install_dir, distribution, pbuilderrc)
        self.lines[label] = new_line
    
    def remove(self, label):

        del self.lines[label]


if __name__ == "__main__":

    if len(sys.argv) >= 2:
    
        command = sys.argv[1]
        config = Config()
        
        if command == "create" and len(sys.argv) == 6:
        
            label, template, install_dir, distribution = sys.argv[2:]
            
            install_distro_dir = os.path.join(install_dir, distribution)
            pbuilderrc = os.path.join(install_distro_dir, "pbuilderrc")
            
            # Check to see if the chroot already exists.
            if config.check(label, template, install_dir, distribution, pbuilderrc):
            
                sys.stderr.write("A chroot already exists with that configuration.\n")
                sys.exit(1)
            
            # Load and fill in a template with installation details.
            details = {"install dir": install_dir,
                       "distribution": distribution}
            
            # Create the installation directory and a pbuilderrc file.
            mkdir(install_dir)
            mkdir(install_distro_dir)
            
            text = open(template, "r").read()
            text = text % details
            write_file(pbuilderrc, text)
            
            # Create the chroot by running pbuilder.
            if os.system("sudo pbuilder create --configfile " + commands.mkarg(pbuilderrc)) == 0:
            
                # Add the chroot to a list in a file in the current directory.
                config.add(template, install_dir, distribution, pbuilderrc)
                config.save()
    
        elif command == "destroy" and len(sys.argv) == 3:
        
            label = sys.argv[2]
            
            # Check to see if the chroot already exists.
            config.check_label(label)
            
            template, install_dir, distribution, pbuilderrc = config.lines[label]
            
            install_distro_dir = os.path.join(install_dir, distribution)
            pbuilderrc = os.path.join(install_distro_dir, "pbuilderrc")
            
            # Remove the installation directory for this distribution.
            if remove_dir(install_distro_dir):
            
                # Remove the chroot from a list in a file in the current directory.
                config.remove(template, install_dir, distribution, pbuilderrc)
                config.save()
    
        elif command == "info" and len(sys.argv) == 3:
        
            label = sys.argv[2]
            
            # Check to see if the chroot already exists.
            config.check_label(label)
            
            template, install_dir, distribution, pbuilderrc = config.lines[label]
            
            print label
            print "Template:          ", template
            print "Installation:      ", install_dir
            print "Distribution:      ", distribution
            print "Configuration file:", pbuilderrc
        
        elif command == "list" and len(sys.argv) == 2:
        
            labels = config.lines.keys()
            labels.sort()
            
            print "\n".join(labels)
        
        elif command == "build" and len(sys.argv) == 4:
        
            label = sys.argv[2]
            name = sys.argv[3]
            
            # Check to see if the chroot already exists.
            config.check_label(label)
            template, install_dir, distribution, pbuilderrc = config.lines[label]
            
            if name.endswith(".dsc"):
            
                # Assume that the other source artifacts are available and just
                # run pbuilder.
                if os.system("sudo pbuilder build --configfile " + \
                             commands.mkarg(pbuilderrc) + " " + \
                             commands.mkarg(name)) == 0:
                
                    products_dir = os.path.join(install_dir, distribution, "cache", "result")
                    print "Build products can be found in", products_dir
            
            else:
                # Try to obtain a source package for the given name.
                directory = tempfile.mkdtemp()
                old_directory = os.path.abspath(os.curdir)
                
                os.chdir(directory)
                print "Fetching source in", directory
                if os.system("apt-get source " + commands.mkarg(name)) == 0:
                
                    if os.system("sudo pbuilder build --configfile " + \
                                 commands.mkarg(pbuilderrc) + " *.dsc") == 0:
                    
                        products_dir = os.path.join(install_dir, distribution, "cache", "result")
                        print "Build products can be found in", products_dir
                
                # Clean up.
                remove_dir(directory)
                os.chdir(old_directory)
    
    else:
        sys.stderr.write("Usage: %s create <label> <template> <install dir> <distribution>\n" % sys.argv[0])
        sys.stderr.write("       %s destroy <label>\n" % sys.argv[0])
        sys.stderr.write("       %s info <label>\n" % sys.argv[0])
        sys.stderr.write("       %s list\n" % sys.argv[0])
        sys.stderr.write("       %s build <label> <package name or .dsc file>\n" % sys.argv[0])
        sys.exit(1)
    
    sys.exit()
