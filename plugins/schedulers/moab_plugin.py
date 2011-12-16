#
# A moab scheduler plugin for hypnotoad.
#

from hypnotoad import plugin
import ldap
import logging

LOG = logging.getLogger('root')

class moab_plugin(plugin.scheduler_plugin):
    def setup(self, config):
        """Called before the plugin is asked to do anything."""
        LOG.debug("Got to moab plugin setup")

        if config.getboolean('Scheduler Options', 'moab_plugin_enabled'):
            LOG.debug("moab plugin enabled")

        self.config = config

    def teardown(self):
        """Called to allow the plugin to free anything."""
        LOG.debug("Got to moab plugin teardown")

    def append_model(self, model):
        """Handled a model appended to this output."""
        LOG.debug("Got to moab plugin append_model.")
