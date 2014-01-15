#!/opt/python27/bin/python

import logging
import sys
import os
import getopt
import ConfigParser

from subprocess import Popen, PIPE
from hypnotoad.core import hypnolog, plugin

PLUGIN_MODEL_VERSION = 1

LOG = logging.getLogger('root')


class PluginLoader(object):

    def load_hypnotoad_plugin(self, path, cls):
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
            module = __import__(modulename)

            # walk the dictionaries to get to the last one
            d = module.__dict__
            for m in modulename.split('.')[1:]:
                d = d[m].__dict__

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

        for dirpath, dirnames, filenames in os.walk(path):
            for name in filenames:
                if name.endswith(".py") and not name.startswith("__"):
                    file_path = os.path.join(
                        os.path.relpath(dirpath, path), name)
                    modulename = "hypnotoad.plugins." + \
                        file_path.rsplit('.', 1)[0].replace('/', '.')
                    look_for_subclass(modulename)

        return plugins

    def send_input_to_output(self, config):
        """
        Get the output of the input plugin and send it to the output plugin.

        @param config: the hypnotoad config
        @type config: ConfigParser
        """
        load_path = os.path.realpath(os.path.dirname(__file__))
        plugin_path = os.path.join(os.path.dirname(load_path), "plugins")

        loaded_datamodel_plugins = []
        loaded_action_plugins = []

        datamodel_outputs = []

        try:
            LOG.debug("Searching `" + str(plugin_path) + "' for plugins.")

            # first, lets find the plugins
            def make_plugins(type):
                return self.load_hypnotoad_plugin(plugin_path, type)
            datamodel_plugins = make_plugins(plugin.data_model_plugin)
            action_plugins = make_plugins(plugin.action_plugin)

            # Now check to see if we have valid plugins.
            LOG.debug("Checking for valid plugins.")

            def check_plugins(plugins):
                if len(plugins) < 1:
                    LOG.error("It looks like we had trouble loading plugins.")
                    sys.exit(1)
            map(check_plugins, [datamodel_plugins, action_plugins])

            # now, run the setup part of each plugin
            def setup_plugins(plugins, out):
                for i in range(len(plugins)):
                    inst = plugins[i]()
                    inst.setup(config, PLUGIN_MODEL_VERSION)
                    out.append(inst)
            setup_plugins(datamodel_plugins, loaded_datamodel_plugins)
            setup_plugins(action_plugins, loaded_action_plugins)

            LOG.debug("Found " + str(len(loaded_datamodel_plugins))
                      + " datamodel plugins.")
            LOG.debug("Found " + str(len(loaded_action_plugins))
                      + " action plugins.")

            # lets get everything from the data models
            for i in range(len(loaded_datamodel_plugins)):
                datamodel_outputs.append(
                    loaded_datamodel_plugins[i].get_model())

            # now we can send the output of the data models to each action
            # plugin
            for i in range(len(loaded_action_plugins)):
                loaded_action_plugins[i].append_model(datamodel_outputs)

            # finally, let the plugins cleanup
            for i in range(len(loaded_datamodel_plugins)):
                loaded_datamodel_plugins[i].teardown()

            for i in range(len(loaded_action_plugins)):
                loaded_action_plugins[i].teardown()
        except:
            print "Unexpected error:", sys.exc_info()[0]
            raise

# EOF
