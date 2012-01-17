#
# A helper for hypnotoad plugins to enable fault tolerant filesystem
# operations.
#

import datetime
import errno
import logging
import os
import subprocess

LOG = logging.getLogger('root')

class hypnofs(object):
    def timeout_command(self, command, timeout=10):
        """
        Call a shell command and either return its output or kill it. Continue
        if the process doesn't get killed cleanly (for D-state).
        """
        start = datetime.datetime.now()
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        while process.poll() is None:
            time.sleep(0.1)
            now = datetime.datetime.now()

            if (now - start).seconds > timeout:
                os.kill(process.pid, signal.SIGKILL)
                os.waitpid(-1, os.WNOHANG)
                raise IOError(errno.EWOULDBLOCK)

        return process.stdout.readlines()

    def makedirs(self, path, timeout=10):
        """A fault tolerant version of os.makedirs()"""
        return self.timeout_command(['mkdir', '-p', path], timeout)

    def chmod(self, path, perms, timeout=10):
        """A fault tolerant version of os.chmod()"""
        return self.timeout_command(['chmod', perms, path], timeout)

    def symlink(self, src, dest, timeout=10):
        """A fault tolerant version of os.symlink()"""
        return self.timeout_command(['ln', '-s', src, dest], timeout)

    def isdir(self, path, timeout=10):
        """A fault tolerant version of os.path.isdir()"""
        cmd_output = self.timeout_command(['file', '-b', path], timeout)
        if "directory" in cmd_output[0]:
            return True
        else:
            return False

    def isfile(self, path, timeout=10):
        """A fault tolerant version of os.path.isfile()"""
        cmd_output = self.timeout_command(['file', '-b', path], timeout)
        if "directory" in cmd_output[0]:
            return False
        elif "ERROR" in cmd_output[0]:
            return False
        else:
            return True

    def islink(self, path, timeout=10):
        """A fault tolerant version of os.path.islink()"""
        cmd_output = self.timeout_command(['file', '-b', path], timeout)
        if "symbolic link" in cmd_output[0]:
            return True
        else:
            return False

    def path_exists(self, path, timeout=10):
        """A fault tolerant version of os.path.exists()"""
        cmd_output = self.timeout_command(['file', '-b', path], timeout)
        if "ERROR" in cmd_output[0]:
            return False
        else:
            return True

    def listdir(self, path, timeout=10):
        """A fault tolerant version of os.listdir()"""
        return self.timeput_command(['find', path, '-maxdepth', '1', '-printf', '"%f\\n"'], timeout)

    def ismount(self, path, timeout=10):
        """A fault tolerant version of os.path.ismount()"""
        cmd_output = self.timeput_command['mountpoint', path], timeout)
        if "is a mountpoint" in cmd_output[0]:
            return True
        else:
            return False

# EOF
