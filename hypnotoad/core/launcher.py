import logging
import sys
import os
import getopt
import ConfigParser

from subprocess import Popen, PIPE

from hypnotoad.core.hypnolog import setup_logger
from hypnotoad.core.plugin_loader import PluginLoader

LOG = setup_logger('root')

def read_config(filename):
    config = ConfigParser.RawConfigParser()
    config.read(filename)

    return config

def usage():
    print """
Usage: hypnotoad [-hvc]

Options:
  -h, --help              show this help message and exit
  -v, --version           print the version and exit
  -c FILE, --config=FILE  use the FILE specified for configuration settings
    """

def which_program(program):
    """
    Determine what executable will be launched by searching environment PATH.
    """
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    return None

def log_version():
    """
    Determine if this is a git repo or an installed package and print out
    the version number.
    """
    git_binary = which_program("git")
    git_child = Popen([git_binary, "rev-parse", "HEAD"], \
        stdout=PIPE, stderr=PIPE)
    git_return = git_child.wait()

    if git_return == 0:
        (git_output, _) = git_child.communicate()
        LOG.critical("hypnotoad-version-git:" + str(git_output).strip())
    else:
        import pkg_resources  # part of setuptools
        version = pkg_resources.require("hypnotoad")[0].version
        LOG.critical("hypnotoad-version-setuptools:" + str(version))

def execute_from_command_line():
    LOG.info("Execution started.")
    parse_command_line_options()
    LOG.info("Execution finished.")

def parse_command_line_options():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hc:v", ["help", "config=", "version"])
    except getopt.GetoptError, err:
        print str(err)
        usage()
        sys.exit(2)

    config = None
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-c", "--config"):
            config = read_config(a)
        elif o in ("-v", "--version"):
            log_version()
            sys.exit()
        else:
            usage()
            assert False, "unhandled option"
            sys.exit(2)

    # Make sure the version is always printed to the logs.
    log_version()

    # Use a default location
    if config is None:
        config = read_config("/etc/hypnotoad.cfg")

    plugin_loader = PluginLoader()
    plugin_loader.send_input_to_output(config)

# EOF
