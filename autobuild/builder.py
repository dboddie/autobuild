
# Copyright (C) 2014 met.no
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import commands, glob, md5, os, stat, tempfile
from debian.deb822 import Changes, Dsc

from config import Config

class AutobuildError(Exception):
    pass

def mkdir(path):

    if os.path.isdir(path):
        print "Directory", path, "already exists."
        return
    
    try:
        os.mkdir(path)
        print "Created", path
    except OSError:
        raise AutobuildError, "Failed to create directory: %s" % path

def rmdir(path):

    try:
        os.rmdir(path)
        print "Removed", path
    except OSError:
        raise AutobuildError, "Failed to remove directory: %s" % path

def remove_dir(path, sudo = False):

    command = "rm -rf " + commands.mkarg(path)
    if sudo:
        command = "sudo " + command
    
    if os.system(command) == 0:
        print "Removed", path, "and its contents."
    else:
        raise AutobuildError, "Failed to remove directory: %s" % path

def remove_file(path, sudo = False):

    command = "rm -f " + commands.mkarg(path)
    if sudo:
        command = "sudo " + command
    
    if os.system(command) == 0:
        print "Removed", path
    else:
        raise AutobuildError, "Failed to remove file: %s" % path

def write_file(path, text):

    try:
        open(path, "w").write(text)
        print "Created", path
    except IOError:
        raise AutobuildError, "Failed to write file: %s" % path


class Builder:

    def __init__(self, config = None):
    
        if config is None:
            config = Config()

        self.config = config
    
    def create(self, label, template, install_dir, distribution, key_id):
    
        install_dir = os.path.abspath(install_dir)
        install_label_dir = os.path.join(install_dir, label)
        install_hooks_dir = os.path.join(install_dir, label, "hooks")
        pbuilderrc = os.path.join(install_label_dir, "pbuilderrc")
        
        # Check to see if the chroot already exists.
        if self.config.check(label, [template, install_dir, distribution, pbuilderrc, key_id]):
        
            raise AutobuildError, "A chroot already exists with that configuration."
        
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
        result = os.system("sudo pbuilder create --configfile " + commands.mkarg(pbuilderrc))
        if result == 0:
        
            # Reopen the configuration file. Really, we should lock the
            # configuration file to prevent others from modifying the file
            # after we have read it.
            
            # Add the chroot to a list in the configuration file.
            self.config.add(label, [template, install_dir, distribution, pbuilderrc, key_id])
            self.config.save()
        
        else:
            # Remove the incomplete installation directory.
            remove_dir(install_label_dir)

        return result
            
    def destroy(self, label):
    
        # Check to see if the chroot already exists.
        self.config.check_label(label)
        
        install_dir = self.config.lines[label][1]
        install_label_dir = os.path.join(install_dir, label)
        
        # Remove the installation directory for this distribution.
        remove_dir(install_label_dir, sudo = False)
        
        # Remove the chroot from a list in the configuration file.
        self.config.remove(label)
        self.config.save()
    
    def update(self, label, options = []):
    
        # Check to see if the chroot already exists.
        self.config.check_label(label)
        
        template, install_dir, distribution, pbuilderrc = self.config.lines[label][:4]
        install_label_dir = os.path.join(install_dir, label)
        
        options = " ".join(map(commands.mkarg, options))
        
        # Update the chroot by running pbuilder.
        if os.system("pbuilder update --configfile " + commands.mkarg(pbuilderrc) + \
                     " " + options) == 0:
            print "chroot '%s' updated successfully." % label
        else:
            raise AutobuildError, "Failed to update chroot '%s'." % label
    
    def login(self, label):
    
        # Check to see if the chroot already exists.
        self.config.check_label(label)
        
        template, install_dir, distribution, pbuilderrc = self.config.lines[label][:4]
        install_label_dir = os.path.join(install_dir, label)
        
        # Log in to the chroot by running pbuilder.
        if os.system("pbuilder login --configfile " + commands.mkarg(pbuilderrc)) != 0:
            raise AutobuildError, "Failed to log in to chroot '%s'." % label
    
    def info(self, label):
    
        # Check to see if the chroot already exists.
        self.config.check_label(label)
        
        values = self.config.lines[label]
        template, install_dir, distribution, pbuilderrc = values[:4]
        if len(values) > 4:
            key_id = values[4]
        else:
            key_id = ""
        
        hooks_dir = os.path.join(install_dir, label, "hooks")
        products_dir = os.path.join(install_dir, label, "cache", "result")
        
        return {"template": template,
                "installation": install_dir,
                "distribution": distribution,
                "configuration": pbuilderrc,
                "hooks": hooks_dir,
                "products": products_dir,
                "signing key": key_id}
    
    def hooks(self, label):
    
        # Check to see if the chroot already exists.
        self.config.check_label(label)
        
        install_dir = self.config.lines[label][1]
        hooks_dir = os.path.join(install_dir, label, "hooks")
        
        hooks = {}
        for name in os.listdir(hooks_dir):
            hooks.setdefault(name[0], []).append(name)
        
        if not hooks:
            return
        
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
    
    def products(self, label):
    
        # Check to see if the chroot already exists.
        self.config.check_label(label)
        
        install_dir = self.config.lines[label][1]
        products_dir = os.path.join(install_dir, label, "cache", "result")
        
        products = {}

        for dsc_path in glob.glob(os.path.join(products_dir, "*.dsc")):
            dsc = Dsc(open(dsc_path).read())
            products.setdefault((dsc["Source"], dsc["Version"]), []).append(dsc)
        
        for changes_path in glob.glob(os.path.join(products_dir, "*.changes")):
            changes = Changes(open(changes_path).read())

            l = products.setdefault((changes["Source"], changes["Version"]), [])
            l.append(changes)
            
            # Append a dictionary describing the changes file itself to the list
            # of products.
            l.append({"Source": changes["Source"],
                      "Version": changes["Version"],
                      "Files": [{"name": os.path.split(changes_path)[1],
                                 "md5sum": md5.md5(open(changes_path, "rb").read()).hexdigest(),
                                 "size": os.stat(changes_path)[stat.ST_SIZE]}]})
        
        return products
    
    def list(self):
    
        labels = self.config.lines.keys()
        labels.sort()
        return labels
    
    def build(self, label, name):
    
        # Check to see if the chroot already exists.
        self.config.check_label(label)
        template, install_dir, distribution, pbuilderrc = self.config.lines[label][:4]
        
        if name.endswith(".dsc"):
        
            # Assume that the other source artifacts are available and just
            # run pbuilder.
            result = os.system("pbuilder build --configfile " + \
                               commands.mkarg(pbuilderrc) + " " + \
                               commands.mkarg(name))
            if result == 0:
                products_dir = os.path.join(install_dir, label, "cache", "result")
                print "Build products can be found in", products_dir
            
            return result
        else:
            # Try to obtain a source package for the given name.
            directory = tempfile.mkdtemp()
            old_directory = os.path.abspath(os.curdir)
            
            os.chdir(directory)
            print "Fetching source in", directory
            result = os.system("apt-get source " + commands.mkarg(name))
            if result == 0:
            
                result = os.system("pbuilder build --configfile " + \
                                   commands.mkarg(pbuilderrc) + " *.dsc")
                if result == 0:
                    products_dir = os.path.join(install_dir, label, "cache", "result")
                    print "Build products can be found in", products_dir
            
            # Clean up.
            remove_dir(directory)
            os.chdir(old_directory)
            return result
    
    def debuild(self, label, build_type = "default"):
    
        # Check to see if the chroot already exists.
        self.config.check_label(label)
        options = self.config.lines[label]
        template, install_dir, distribution, pbuilderrc = options[:4]
        
        # Check that we are in a package source directory before running pdebuild.
        if not os.path.isdir("debian"):
            return 1
        
        config_args = "--configfile " + commands.mkarg(pbuilderrc)

        # Run pdebuild with options for signing if a key ID was supplied.
        if len(options) == 5:
            key_id = options[4]
            key_sign_args = "--auto-debsign --debsign-k " + commands.mkarg(key_id)
        else:
            key_sign_args = ""
        
        if build_type == "source":
            pdebuild = "autobuild-pdebuild"
            build_type_args = '--debbuildopts "-S -sa"'
        elif build_type == "source-changes":
            pdebuild = "autobuild-pdebuild"
            build_type_args = '--debbuildopts "-S -sd"'
        else:
            pdebuild = "pdebuild"
            build_type_args = ""

        result = os.system("sudo " + pdebuild + " " + key_sign_args + \
                               " " + config_args + " " + build_type_args)
        if result == 0:
            products_dir = os.path.join(install_dir, label, "cache", "result")
            print "Build products can be found in", products_dir

        return result
    
    def _files(self, label, name, version = None):
    
        # Check to see if the chroot already exists.
        self.config.check_label(label)
        install_dir = self.config.lines[label][1]
        products_dir = os.path.join(install_dir, label, "cache", "result")
        
        # Find the .dsc and .changes files for the named package.
        if version is not None:
            pattern = name + "_" + version + "*"

        names = glob.glob(os.path.join(products_dir, pattern + ".changes"))
        if len(names) != 1:
            raise AutobuildError, "Unable to find a unique match for '%s'." % name
        
        changes_path = names[0]
        
        names = glob.glob(os.path.join(products_dir, pattern + ".dsc"))
        if len(names) != 1:
            raise AutobuildError, "Unable to find a unique match for '%s'." % name
        
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
        
        return files
    
    def remove(self, label, name, version = None):
    
        # Check to see if the chroot already exists.
        self.config.check_label(label)
        install_dir = self.config.lines[label][1]
        products_dir = os.path.join(install_dir, label, "cache", "result")

        # Delete the files associated with this package.
        for file_name in self._files(label, name, version):
            remove_file(os.path.join(products_dir, file_name), sudo = False)

    def files(self, label, name, version = None):
    
        # Check to see if the chroot already exists.
        self.config.check_label(label)
        install_dir = self.config.lines[label][1]
        products_dir = os.path.join(install_dir, label, "cache", "result")
        
        # Print a list of the files associated with this package.
        for file_name in self._files(label, name, version):
            print os.path.join(products_dir, file_name)
