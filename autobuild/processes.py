import os, stat
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
        stdout_path, stderr_path, result_path = output_paths(path)
        
        if os.path.exists(path):
            return "Building"
        elif os.path.exists(result_path):
            result = open(result_path).read().strip()
            if result == "0":
                return "Built"
            else:
                return "Failed"
        else:
            return "Not built"

manager = Processes()
