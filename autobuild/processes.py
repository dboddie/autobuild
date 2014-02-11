import os
import config

def claim_process(chroot, repo):

    c = config.Config("autobuild-building", load = False)
    f = open(c.path)
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

    except (KeyError, ValueError):
        # No label exists, so continue with the process.
        pass

    return c, f

def update_process(cf, chroot, repo, pid):

    c, f = cf
    label = chroot + "-" + repo
    c.remove(label)
    c.add(label, [str(pid)])
    c._save(f)
    c.unlock(f)
    f.close()
