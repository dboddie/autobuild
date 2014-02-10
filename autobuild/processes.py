import os
import config

def claim_process(lock, chroot, repo):

    c = config.Config(path = lock.path)
    label = chroot + "-" + repo

    try:
        [pid] = c.lines[label]

        pid = int(pid)

        pid_status = os.waitpid(pid, os.WNOHANG)
        if pid_status == (0, 0):
            # Still running/no information.
            return False

    except (KeyError, ValueError):
        pass

    return True

def update_process(lock, chroot, repo, pid):

    c = config.Config(path = lock.path)
    label = chroot + "-" + repo
    c.add(label, ["None"])
    c.save()

def remove_process(chroot, repo):

    del processes[(chroot, repo)]
