#!/usr/bin/env python

import logging
import sys
import os
import getopt
import ConfigParser

from hypnotoad import hypnolog, plugin

def load_hypnotoad_plugin(path, cls):
    """
    Find the first subclass of cls with name in py files located below path
    (does look in sub directories)
 
    @param path: the path to the top level folder to walk
    @type path: str
    @param cls: the base class that the subclass should inherit from
    @type cls: class
    @rtype: arr
    @return: all plugins with subclass of cls
    """

    plugins = []
 
    def look_for_subclass(modulename):
        module=__import__(modulename)
 
        # walk the dictionaries to get to the last one
        d=module.__dict__
        for m in modulename.split('.')[1:]:
            d=d[m].__dict__
 
        # look through this dictionary for things
        # that are subclass of cls
        # but are not cls itself
        for key, entry in d.items():
            if key == cls.__name__:
                continue
 
            try:
                if issubclass(entry, cls):
                    LOG.debug("Found plugin: " + key)
                    plugins.append(entry)
            except TypeError:
                # this happens when a non-type is passed in to issubclass. We
                # don't care as it can't be a subclass of cls if it isn't a
                # type
                continue
 
    for root, dirs, files in os.walk(path):
        for name in files:
            if name.endswith(".py") and not name.startswith("__"):
                path = os.path.join(root, name)
                modulename = path.rsplit('.', 1)[0].replace('/', '.')
                look_for_subclass(modulename)

    return plugins

def send_input_to_output(config):
    """
    Get the output of the input plugin and send it to the output plugin.

    @param config: the hypnotoad config
    @type config: ConfigParser
    """

    plugin_path = config.get('Basic Options', 'plugins_dir')

    loaded_datamodel_plugins = []
    loaded_scheduler_plugins = []

    datamodel_user_outputs = []
    datamodel_priority_outputs = []

    try:

        # first, lets find the plugins
        datamodel_plugins = load_hypnotoad_plugin(plugin_path, plugin.data_model_plugin)
        scheduler_plugins = load_hypnotoad_plugin(plugin_path, plugin.scheduler_plugin)

        if len(datamodel_plugins) < 1:
            LOG.error("It doesn't look like we've found any data model plugins.")
            sys.exit(1)
        if len(scheduler_plugins) < 1:
            LOG.error("It doesn't look like we've found any scheduler plugins.")
            sys.exit(1)

        # now, run the setup part of each plugin
        for i in range(len(datamodel_plugins)):
            inst = datamodel_plugins[i]()
            inst.setup(config)
            loaded_datamodel_plugins.append(inst)

        for i in range(len(scheduler_plugins)):
            inst = scheduler_plugins[i]()
            inst.setup(config)
            loaded_scheduler_plugins.append(inst)

        LOG.debug("Loaded (" + str(len(loaded_datamodel_plugins)) + ") datamodel plugins.")
        LOG.debug("Loaded (" + str(len(loaded_scheduler_plugins)) + ") scheduler plugins.")

        # lets get everything from the data models
        for i in range(len(loaded_datamodel_plugins)):
            datamodel_user_outputs.append(loaded_datamodel_plugins[i].user_info())
            datamodel_priority_outputs.append(loaded_datamodel_plugins[i].priority_info())

        # now we can send the output of the data models to each scheduler plugin
        for i in range(len(loaded_scheduler_plugins)):
            loaded_scheduler_plugins[i].user_output(datamodel_user_outputs)
            loaded_scheduler_plugins[i].priority_output(datamodel_priority_outputs)

        # finally, let the plugins cleanup
        for i in range(len(loaded_datamodel_plugins)):
            loaded_datamodel_plugins[i].teardown()

        for i in range(len(loaded_scheduler_plugins)):
            loaded_scheduler_plugins[i].teardown()
    except:
        print "Unexpected error:", sys.exc_info()[0]
        raise

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

def main():
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
    LOG.debug("Execution started.")
    main()
    LOG.debug("Execution finished.")
