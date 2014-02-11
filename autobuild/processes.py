import os
import config

def claim_process(chroot, repo):

    c = config.Config("autobuild-building", load = False)
    f = open(c.path)
    c.lock(f)
    c._load()

    label = chroot + "-" + repo

    try:
        [pid] = c.lines[label]

        if pid == "None":
            # Another process is being set up.
            c.unlock(f)
            f.close()
            return False

        pid = int(pid)

        pid_status = os.waitpid(pid, os.WNOHANG)
        if pid_status == (0, 0):
            # Still running/no information.
            c.unlock(f)
            f.close()
            return False

    except KeyError:
        # No label exists, so continue with the process.
        pass

    c.add(label, ["None"])
    c._save()
    c.unlock(f)
    f.close()
    return True

def update_process(chroot, repo, pid):

    c = config.Config("autobuild-building", load = False)
    f = open(c.path, "w")
    c.lock(f)
    c._load()

    label = chroot + "-" + repo
    c.remove(label)
    c.add(label, [pid])
    c._save()
    c.unlock(f)
    f.close()
