
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

import fcntl, os, sys

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
        
            if line.startswith("#"):
                continue

            at = line.find(": ")
            if at == -1:
                continue

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

