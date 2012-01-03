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

    datamodel_outputs = []

    try:

        # first, lets find the plugins
        def make_plugins(type): return load_hypnotoad_plugin(plugin_path, type)
        datamodel_plugins = make_plugins(plugin.data_model_plugin)
        scheduler_plugins = make_plugins(plugin.scheduler_plugin)

        # Now check to see if we have valid plugins.
        def check_plugins(plugins):
            if len(plugins) < 1:
                LOG.error("It looks like we had trouble loading plugins.")
                sys.exit(1)
        map(check_plugins, [datamodel_plugins, scheduler_plugins])

        # now, run the setup part of each plugin
        def setup_plugins(plugins, out):
            for i in range(len(plugins)):
                inst = plugins[i]()
                inst.setup(config)
                out.append(inst)
        setup_plugins(datamodel_plugins, loaded_datamodel_plugins)
        setup_plugins(scheduler_plugins, loaded_scheduler_plugins)

        LOG.debug("Loaded (" + str(len(loaded_datamodel_plugins)) + ") datamodel plugins.")
        LOG.debug("Loaded (" + str(len(loaded_scheduler_plugins)) + ") scheduler plugins.")

        # lets get everything from the data models
        for i in range(len(loaded_datamodel_plugins)):
            datamodel_outputs.append(loaded_datamodel_plugins[i].get_model())

        # now we can send the output of the data models to each scheduler plugin
        for i in range(len(loaded_scheduler_plugins)):
            loaded_scheduler_plugins[i].append_model(datamodel_outputs)

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

def version():
    LOG.debug(os.popen("git rev-parse HEAD").read())
    LOG.debug(os.popen("git log --branches --not --remotes").read())

def main():
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
    LOG.debug("Execution started.")
    main()
    LOG.debug("Execution finished.")
