import os
import config

def claim_process(chroot, repo):

    c = config.Config("autobuild-building", load = False)
    if not os.path.exists(c.path):
        open(c.path, "w").write("")

    f = open(c.path, "r+w")
    c.lock(f)
    c._load(f)

    label = chroot + "-" + repo

    try:
        [pid] = c.lines[label]

        pid = int(pid)

        pid_status = os.waitpid(pid, os.WNOHANG)
        if pid_status == (0, 0):
            # Still running/no information.
            c.unlock(f)
            f.close()
            return None

    except (KeyError, OSError, ValueError):
        # No label exists, the child process is missing, or the
        # pid is invalid, so continue with the process.
        pass

    return c, f

def update_process(cf, chroot, repo, pid):

    c, f = cf
    label = chroot + "-" + repo
    c.add(label, [str(pid)])
    c._save(f)
    c.unlock(f)
    f.close()
