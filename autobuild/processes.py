import os, shutil, stat, tempfile

class Manager:

    def __init__(self):

        self.temp_dir = tempfile.mkdtemp()
    
    def __del__(self):

        shutil.rmtree(temp_dir)

    def claim_process(self, chroot, repo):
    
        label = chroot + "-" + repo
        
        # Try to create a file.
        path = os.path.join(self.temp_dir, label)
        try:
            os.mknod(path, 0644, stat.S_IFREG)

        except OSError:
            return None
        
        return path
    
    def update_process(self, path, pid):
    
        open(path, "w").write(str(pid))
