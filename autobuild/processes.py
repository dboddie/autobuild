import os, stat

temp_dir = "/tmp"
    
def claim_process(chroot, repo):

    label = chroot + "-" + repo
    
    # Try to create a file.
    path = os.path.join(temp_dir, label)
    try:
        os.mknod(path, 0644, stat.S_IFREG)

    except OSError:
        return None
    
    return path

def update_process(path, pid):

    open(path, "w").write(str(pid))

def remove_lockfile(path):

    os.remove(path)

def is_building(chroot, repo):

    label = chroot + "-" + repo
    path = os.path.join(temp_dir, label)
    return os.path.exists(path)
