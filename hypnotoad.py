#!/usr/bin/env python

import logging
import sys
import os
import getopt
import ConfigParser

from hypnotoad import plugin
from hypnotoad import hypnolog

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
        LOG.debug("Searching %s" % (modulename))
        module=__import__(modulename)
 
        #walk the dictionaries to get to the last one
        d=module.__dict__
        for m in modulename.split('.')[1:]:
            d=d[m].__dict__
 
        #look through this dictionary for things
        #that are subclass of Job
        #but are not Job itself
        for key, entry in d.items():
            if key == cls.__name__:
                continue
 
            try:
                if issubclass(entry, cls):
                    LOG.debug("Found plugin:" + key)
                    plugins.append(entry)
            except TypeError:
                #this happens when a non-type is passed in to issubclass. We
                #don't care as it can't be a subclass of Job if it isn't a
                #type
                continue
 
    for root, dirs, files in os.walk(path):
        for name in files:
            if name.endswith(".py") and not name.startswith("__"):
                path = os.path.join(root, name)
                modulename = path.rsplit('.', 1)[0].replace('/', '.')
                look_for_subclass(modulename)

    # We didn't find anything if we get here.
    return plugins

def send_input_to_output(config):
    """
    Get the output of the input plugin and send it to the output plugin.

    @param config: the hypnotoad config
    @type config: ConfigParser
    """

    plugin_path = config.get('Basic Options', 'plugins_dir')

    try:
        datamodel = load_hypnotoad_plugin(plugin_path, plugin.data_model_plugin)
        scheduler = load_hypnotoad_plugin(plugin_path, plugin.scheduler_plugin)

        if datamodel is None:
            LOG.error("Failed loading a data model plugin: " + str(input_plugin_name))
            sys.exit(1)
        if scheduler is None:
            LOG.error("Failed loading a scheduler plugin: " + str(output_plugin_name))
            sys.exit(1)

        datamodel.setup()
        scheduler.setup()

        uinfo = datamodel.user_info()
        pinfo = datamodel.priority_info()

        if uinfo is None:
            LOG.error("Data model user info is invalid.")
            sys.exit(1)
        if pinfo is None:
            LOG.error("Data model priority info is invalid.")
            sys.exit(1)

        print scheduler.user_output(uinfo)
        print scheduler.priority_output(pinfo)

        datamodel.teardown() 
        scheduler.teardown()

    except:
        print "Unexpected error:", sys.exc_info()[0]
        raise

def read_config(filename):
    config = ConfigParser.RawConfigParser()
    config.read(filename)

    return config

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
            assert False, "unhandled option"

    # Use the default location
    if config is None:
        config = read_config("hypnotoad.cfg")

    send_input_to_output(config)

LOG = hypnolog.setup_logger('root')
if __name__ == "__main__":
    main()
