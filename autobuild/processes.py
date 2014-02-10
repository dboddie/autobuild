import os
import config

processes = {}

def claim_process(chroot, repo):

    print processes
    try:
        pid = processes[(chroot, repo)]

        if pid is None:
            # A process is being started.
            return False

        pid_status = os.wait(pid, os.WNOHANG)
        if pid_status == (0, 0):
            # Still running/no information.
            return False

    except KeyError:
        pass

    processes[(chroot, repo)] = None
    return True

def update_process(chroot, repo, pid):

    processes[(chroot, repo)] = pid

def remove_process(chroot, repo):

    del processes[(chroot, repo)]
