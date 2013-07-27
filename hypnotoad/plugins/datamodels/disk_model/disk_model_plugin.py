#
# A disk based data model plugin for hypnotoad.
#

import logging

from hypnotoad.core import plugin

LOG = logging.getLogger('root')

class disk_model_plugin(plugin.data_model_plugin):
    def setup(self, config, model_version):
        """Called before the plugin is asked to do anything."""

        if config.getboolean('Data Model Options', 'disk_model_plugin_enabled'):
            self.plugin_enabled = True
            LOG.debug("Disk model plugin enabled")

            self.config = config
            self.model_version = model_version
        else:
            self.plugin_enabled = False

    def teardown(self):
        """Called to allow the plugin to free anything."""

        if self.plugin_enabled:
            LOG.debug("Got to disk model plugin teardown")
            self.ldap_ctx.unbind_s()

    def get_model(self):
        """Look up information in this data model."""

        model = []

        if self.plugin_enabled:
            LOG.debug("Got to disk model plugin get_model")

        return model

# EOF
