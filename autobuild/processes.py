import fcntl, os
import config

def claim_process(chroot, repo):

    c = config.Config("autobuild-building", load = False)
    f = open(c.path)
    c.lock()
    c._load()

    label = chroot + "-" + repo

    try:
        [pid] = c.lines[label]

        pid = int(pid)

        pid_status = os.waitpid(pid, os.WNOHANG)
        if pid_status == (0, 0):
            # Still running/no information.
            c.unlock()
            f.close()
            return False

    except (KeyError, ValueError):
        pass

    c.add(label, ["None"])
    c._save()
    c.unlock()
    f.close()
    return True

def update_process(chroot, repo, pid):

    c = config.Config("autobuild-building", load = False)
    f = open(c.path, "w")
    c.lock()
    c._load()

    label = chroot + "-" + repo
    c.remove(label)
    c.add(label, [pid])
    c._save()
    c.unlock()
    f.close()

def unlock():

    path = os.path.join(os.getenv("HOME"), ".autobuild-building")
    f = open(path
    fcntl.flock(
