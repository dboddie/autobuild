
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

import os, stat, time
import config

class Processes:

    def __init__(self):
    
        c = config.Config("autobuild-processes")
        c.load()
        [self.temp_dir] = c.lines.get("temporary directory", "/tmp")
        if not os.path.exists(self.temp_dir):
            os.mkdir(self.temp_dir)
    
    def process_path(self, chroot, repo):
    
        return chroot + "-" + repo
    
    def claim_process(self, chroot, repo):
    
        label = self.process_path(chroot, repo)
    
        # Try to create a file.
        path = os.path.join(self.temp_dir, label)
        try:
            os.mknod(path, 0644, stat.S_IFREG)
    
        except OSError:
            return None
        
        return path
    
    def output_paths(self, path):
    
        stdout_path = path + ".stdout"
        stderr_path = path + ".stderr"
        result_path = path + ".result"
    
        return stdout_path, stderr_path, result_path
    
    def update_process(self, path, pid):
    
        open(path, "w").write(str(pid))
    
    def remove_lockfile(self, path):
    
        os.remove(path)
    
    def status(self, chroot, repo):
    
        label = self.process_path(chroot, repo)
    
        path = os.path.join(self.temp_dir, label)
        stdout_path, stderr_path, result_path = self.output_paths(path)

        # Instead of checking that the lock file exists then querying its
        # creation time, just check the creation time. This avoids a race
        # condition that could occur if the file was deleted between the
        # initial check and stat call.
        try:
            time_str = time.strftime("%Y-%m-%d %H:%M:%S %Z", time.localtime(os.stat(path)[stat.ST_CTIME]))
            return "Building", time_str
        except OSError:
            pass
        
        try:
            time_str = time.strftime("%Y-%m-%d %H:%M:%S %Z", time.localtime(os.stat(result_path)[stat.ST_MTIME]))
            result = open(result_path).read().strip()
            if result == "0":
                return "Built", time_str
            else:
                return "Failed", time_str

        except (IOError, OSError):
            return "Not built", None

manager = Processes()
