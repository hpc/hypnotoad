#
# An action plugin for hypnotoad to create new user directories.
#

import logging
import os
import sys

sys.path.append(os.path.abspath('plugins/actions/userdirs'))

from hypnotoad.core import plugin

LOG = logging.getLogger('root')


class userdirs_plugin(plugin.action_plugin):

    def setup(self, config, model_version):
        """Called before the plugin is asked to do anything."""
        if config.getboolean('Action Options', 'userdirs_plugin_enabled'):
            self.plugin_enabled = True
            LOG.debug("User directory creation plugin enabled")

            self.config = config
            self.model_version = model_version
        else:
            self.plugin_enabled = False

    def teardown(self):
        """Called to allow the plugin to free anything."""
        if self.plugin_enabled:
            LOG.debug("Got to user directory creation plugin teardown")

    def append_model(self, models):
        """Handle a model appended to this output."""
        if self.plugin_enabled:
            LOG.debug("Got to user directory creation plugin append_model.")

            # Make sure we're not trying to change too many things compared
            # to the last run.
            userdirs.check_if_unsafe_model_difference(self.config, models)

            # Create missing user directories.
            userdirs.create_missing_user_directories(self.config, models)

            # Determine what files aren't supposed to be there.
            userdirs.report_unknown_files(self.config, models)

# EOF
