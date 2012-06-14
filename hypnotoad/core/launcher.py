import logging
import sys
import os
import getopt
import ConfigParser

from subprocess import Popen, PIPE

import hypnolog, plugin

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

def version():
    LOG.critical("git:" + os.popen("git rev-parse HEAD").read().strip())

def execute_from_command_line():
    version()

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
        config = read_config("hypnotoad.cfg")

    send_input_to_output(config)

LOG = hypnolog.setup_logger('root')
if __name__ == "__main__":
    LOG.info("Execution started.")
    main()
    LOG.info("Execution finished.")

# EOF
