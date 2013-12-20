#!/usr/bin/env python

import commands, os, sys

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

def write_file(path, text):

    try:
        open(path, "w").write(text)
        print "Created", path
    except IOError:
        sys.stderr.write("Failed to write file: %s\n" % path)
        sys.exit(1)

class Config:

    def __init__(self):
    
        self.path = "active"
        self.load()
    
    def load(self):
    
        try:
            self.lines = set(open(self.path).readlines())
        except IOError:
            self.lines = set()
    
    def save(self):
    
        try:
            f = open(self.path, "w")
            for line in self.lines:
                f.write(line)
            f.close()
        except IOError:
            sys.stderr.write("Failed to update the list of active chroots.\n")
    
    def make_line(self, *args):
    
        return " ".join(args) + "\n"
    
    def check(self, template, install_dir, distribution, pbuilderrc):

        new_line = self.make_line(template, install_dir, distribution, pbuilderrc)
        return new_line in self.lines
    
    def add(self, template, install_dir, distribution, pbuilderrc):
    
        new_line = self.make_line(template, install_dir, distribution, pbuilderrc)
        self.lines.add(new_line)
    
    def remove(self, template, install_dir, distribution, pbuilderrc):

        old_line = self.make_line(template, install_dir, distribution, pbuilderrc)
        self.lines.remove(old_line)


if __name__ == "__main__":

    if len(sys.argv) >= 2:
    
        command = sys.argv[1]
        
        if command == "create" and len(sys.argv) == 5:
        
            template, install_dir, distribution = sys.argv[2:]
            
            install_distro_dir = os.path.join(install_dir, distribution)
            pbuilderrc = os.path.join(install_distro_dir, "pbuilderrc")
            
            # Check to see if the chroot already exists.
            config = Config()
            if config.check(template, install_dir, distribution, pbuilderrc):
            
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
            if os.system("sudo pbuilder create --configfile %s" % pbuilderrc) == 0:
            
                # Add the chroot to a list in a file in the current directory.
                config.add(template, install_dir, distribution, pbuilderrc)
                config.save()
    
        elif command == "destroy" and len(sys.argv) == 5:
        
            template, install_dir, distribution = sys.argv[2:]
            
            install_distro_dir = os.path.join(install_dir, distribution)
            pbuilderrc = os.path.join(install_distro_dir, "pbuilderrc")
            
            # Check to see if the chroot already exists.
            config = Config()
            if not config.check(template, install_dir, distribution, pbuilderrc):
            
                sys.stderr.write("No chroot exists with that configuration.\n")
                sys.exit(1)
            
            # Remove the installation directory for this distribution.
            if os.system("sudo rm -rf " + commands.mkarg(install_distro_dir)) == 0:
            
                # Remove the chroot from a list in a file in the current directory.
                config.remove(template, install_dir, distribution, pbuilderrc)
                config.save()
    
    else:
        sys.stderr.write("Usage: %s create <template> <install dir> <distribution>\n" % sys.argv[0])
        sys.stderr.write("Usage: %s destroy <template> <install dir> <distribution>\n" % sys.argv[0])
        sys.exit(1)
    
    sys.exit()
