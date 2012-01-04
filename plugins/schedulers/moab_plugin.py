#
# A moab scheduler plugin for hypnotoad.
#

from hypnotoad import plugin
import ldap
import logging

LOG = logging.getLogger('root')

class moab_plugin(plugin.scheduler_plugin):
    def setup(self, config, model_version):
        """Called before the plugin is asked to do anything."""

        if config.getboolean('Scheduler Options', 'moab_plugin_enabled'):
            self.plugin_enabled = True
            LOG.debug("moab plugin enabled")

            self.config = config
            self.model_version = model_version
        else:
            self.plugin_enabled = False

    def teardown(self):
        """Called to allow the plugin to free anything."""

        if self.plugin_enabled:
            LOG.debug("Got to moab plugin teardown")

    def append_model(self, model):
        """Handled a model appended to this output."""

        if self.plugin_enabled:
            LOG.debug("Got to moab plugin append_model.")
