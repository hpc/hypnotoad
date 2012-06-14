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
Usage: hypnotoad [-hc]

Options:
  -h, --help              show this help message and exit
  -c FILE, --config=FILE  use the FILE specified for configuration settings
    """

def log_version():
    LOG.critical("git:" + os.popen("git rev-parse HEAD").read().strip())

def execute_from_command_line():
    LOG.info("Execution started.")
    log_version()
    parse_command_line_options()
    LOG.info("Execution finished.")

def parse_command_line_options():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hc:", ["help", "config="])
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
        else:
            usage()
            assert False, "unhandled option"
            sys.exit(2)

    # Use a default location
    if config is None:
        config = read_config("/etc/hypnotoad.cfg")

    plugin_loader = PluginLoader()
    plugin_loader.send_input_to_output(config)

# EOF
