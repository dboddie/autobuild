#!/usr/bin/env python

import commands, glob, os, sys, tempfile
from debian.deb822 import Changes, Dsc

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

def remove_dir(path, sudo = False):

    command = "rm -rf " + commands.mkarg(path)
    if sudo:
        command = "sudo " + command
    
    if os.system(command) == 0:
        print "Removed", path, "and its contents."
        return True
    else:
        sys.stderr.write("Failed to remove directory: %s\n" % path)
        return False

def remove_file(path, sudo = False):

    command = "rm -f " + commands.mkarg(path)
    if sudo:
        command = "sudo " + command
    
    if os.system(command) == 0:
        print "Removed", path
        return True
    else:
        sys.stderr.write("Failed to remove file: %s\n" % path)
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
    
        home_dir = os.getenv("HOME", os.path.split(os.path.abspath(__file__))[0])
        self.path = os.path.join(home_dir, ".autobuild")
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
    
    def check(self, label, template, install_dir, distribution, pbuilderrc):
    
        if label in self.lines:
            return True
        
        new_line = [template, install_dir, distribution, pbuilderrc]
        
        return new_line in self.lines.values()
    
    def check_label(self, label):
    
        if not label in self.lines:
        
            sys.stderr.write("No chroot exists with that configuration.\n")
            sys.exit(1)
    
    def add(self, label, template, install_dir, distribution, pbuilderrc):
    
        new_line = [template, install_dir, distribution, pbuilderrc]
        self.lines[label] = new_line
    
    def remove(self, label):

        del self.lines[label]


if __name__ == "__main__":

    if len(sys.argv) >= 2:
    
        command = sys.argv[1]
        config = Config()
        
        if command == "create" and len(sys.argv) == 6:
        
            label, template, install_dir, distribution = sys.argv[2:]
            
            install_label_dir = os.path.join(install_dir, label)
            install_hooks_dir = os.path.join(install_dir, label, "hooks")
            pbuilderrc = os.path.join(install_label_dir, "pbuilderrc")
            
            # Check to see if the chroot already exists.
            if config.check(label, template, install_dir, distribution, pbuilderrc):
            
                sys.stderr.write("A chroot already exists with that configuration.\n")
                sys.exit(1)
            
            # Load and fill in a template with installation details.
            details = {"install dir": install_dir,
                       "label": label,
                       "distribution": distribution}
            
            # Create the installation directories and a pbuilderrc file.
            mkdir(install_dir)
            mkdir(install_label_dir)
            mkdir(install_hooks_dir)
            
            text = open(template, "r").read()
            text = text % details
            write_file(pbuilderrc, text)
            
            # Create the chroot by running pbuilder.
            if os.system("sudo pbuilder create --configfile " + commands.mkarg(pbuilderrc)) == 0:
            
                # Reopen the configuration file. Really, we should lock the
                # configuration file to prevent others from modifying the file
                # after we have read it.
                config = Config()
                
                # Add the chroot to a list in a file in the current directory.
                config.add(label, template, install_dir, distribution, pbuilderrc)
                config.save()
            
            sys.exit()
    
        elif command == "destroy" and len(sys.argv) == 3:
        
            label = sys.argv[2]
            
            # Check to see if the chroot already exists.
            config.check_label(label)
            
            template, install_dir, distribution, pbuilderrc = config.lines[label]
            
            install_label_dir = os.path.join(install_dir, label)
            pbuilderrc = os.path.join(install_label_dir, "pbuilderrc")
            
            # Remove the installation directory for this distribution.
            if remove_dir(install_label_dir, sudo = True):
            
                # Remove the chroot from a list in a file in the current directory.
                config.remove(label)
                config.save()
            
            sys.exit()
    
        elif command == "update" and len(sys.argv) == 3:
        
            label = sys.argv[2]
            
            # Check to see if the chroot already exists.
            config.check_label(label)
            
            template, install_dir, distribution, pbuilderrc = config.lines[label]
            
            install_label_dir = os.path.join(install_dir, label)
            pbuilderrc = os.path.join(install_label_dir, "pbuilderrc")
            
            # Update the chroot by running pbuilder.
            if os.system("sudo pbuilder update --configfile " + commands.mkarg(pbuilderrc)) == 0:
                print "chroot '%s' updated successfully." % label
            else:
                sys.stderr.write("Failed to update chroot '%s'.\n" % label)
                sys.exit(1)
            
            sys.exit()
    
        elif command == "info" and len(sys.argv) == 3:
        
            label = sys.argv[2]
            
            # Check to see if the chroot already exists.
            config.check_label(label)
            
            template, install_dir, distribution, pbuilderrc = config.lines[label]
            hooks_dir = os.path.join(install_dir, label, "hooks")
            products_dir = os.path.join(install_dir, label, "cache", "result")
            
            print label
            print "Template:          ", template
            print "Installation:      ", install_dir
            print "Distribution:      ", distribution
            print "Configuration file:", pbuilderrc
            print "Hooks directory:   ", hooks_dir
            print "Products directory:", products_dir
            sys.exit()
        
        elif command == "hooks" and len(sys.argv) == 3:
        
            label = sys.argv[2]
            
            # Check to see if the chroot already exists.
            config.check_label(label)
            
            template, install_dir, distribution, pbuilderrc = config.lines[label]
            hooks_dir = os.path.join(install_dir, label, "hooks")
            
            hooks = {}
            for name in os.listdir(hooks_dir):
                hooks.setdefault(name[0], []).append(name)
            
            if not hooks:
                sys.exit()
            
            print hooks_dir
            
            for prefix, desc in (("D", "Before unpacking build system"),
                                 ("A", "Before building"),
                                 ("B", "After a successful build"),
                                 ("C", "After a failed build")):
            
                names = hooks.get(prefix, [])
                
                if names:
                    names.sort()
                    print
                    print desc + ":"
                    
                    for name in names:
                        print " ", name
            
            sys.exit()
        
        elif command == "products" and len(sys.argv) == 3:
        
            label = sys.argv[2]
            
            # Check to see if the chroot already exists.
            config.check_label(label)
            
            template, install_dir, distribution, pbuilderrc = config.lines[label]
            products_dir = os.path.join(install_dir, label, "cache", "result")
            
            for dsc_path in glob.glob(os.path.join(products_dir, "*.dsc")):
                dsc = Dsc(open(dsc_path).read())
                print dsc["Source"], dsc["Version"]
            
            sys.exit()
        
        elif command == "list" and len(sys.argv) == 2:
        
            labels = config.lines.keys()
            labels.sort()
            
            print "\n".join(labels)
            sys.exit()
        
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
                
                    products_dir = os.path.join(install_dir, label, "cache", "result")
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
                    
                        products_dir = os.path.join(install_dir, label, "cache", "result")
                        print "Build products can be found in", products_dir
                
                # Clean up.
                remove_dir(directory)
                os.chdir(old_directory)
            
            sys.exit()
    
        elif command == "remove" and len(sys.argv) == 4:
        
            label = sys.argv[2]
            name = sys.argv[3]
            
            # Check to see if the chroot already exists.
            config.check_label(label)
            template, install_dir, distribution, pbuilderrc = config.lines[label]
            products_dir = os.path.join(install_dir, label, "cache", "result")
            
            # Find the .dsc and .changes files for the named package.
            names = glob.glob(os.path.join(products_dir, name + "*.changes"))
            if len(names) != 1:
                sys.stderr.write("Unable to find a unique match for '%s'.\n" % name)
                sys.exit(1)
            
            changes_path = names[0]
            
            names = glob.glob(os.path.join(products_dir, name + "*.dsc"))
            if len(names) != 1:
                sys.stderr.write("Unable to find a unique match for '%s'.\n" % name)
                sys.exit(1)
            
            dsc_path = names[0]
            
            # Open the files and locate the other build products.
            changes = Changes(open(changes_path).read())
            dsc = Dsc(open(dsc_path).read())
            
            # Collect the file names of the files associated with this package.
            files = set([changes_path, dsc_path])
            
            for section in ("Checksums-Sha1", "Checksums-Sha256", "Files"):
            
                for desc in changes, dsc:
                    try:
                        for entry in desc[section]:
                            files.add(entry["name"])
                    except KeyError:
                        pass
            
            # Delete the files associated with this package.
            for file_name in files:
                remove_file(os.path.join(products_dir, file_name), sudo = True)
            
            sys.exit()
    
    sys.stderr.write("Usage: %s create <label> <template> <install dir> <distribution>\n" % sys.argv[0])
    sys.stderr.write("       %s destroy <label>\n" % sys.argv[0])
    sys.stderr.write("       %s update <label>\n" % sys.argv[0])
    sys.stderr.write("       %s info <label>\n" % sys.argv[0])
    sys.stderr.write("       %s hooks <label>\n" % sys.argv[0])
    sys.stderr.write("       %s products <label>\n" % sys.argv[0])
    sys.stderr.write("       %s list\n" % sys.argv[0])
    sys.stderr.write("       %s build <label> <package name or .dsc file>\n" % sys.argv[0])
    sys.stderr.write("       %s remove <label> <package name>\n" % sys.argv[0])
    sys.exit(1)
