#
# A slurm priority action plugin for hypnotoad.
#

import logging
import os
import sys

sys.path.append(os.path.abspath('plugins/actions/slurm'))

from hypnotoad import plugin

LOG = logging.getLogger('root')

class slurm_plugin(plugin.action_plugin):
    def setup(self, config, model_version):
        """Called before the plugin is asked to do anything."""

        if config.getboolean('Action Options', 'slurm_plugin_enabled'):
            self.plugin_enabled = True
            LOG.debug("slurm plugin enabled")

            self.config = config
            self.model_version = model_version
        else:
            self.plugin_enabled = False

    def teardown(self):
        """Called to allow the plugin to free anything."""

        if self.plugin_enabled:
            LOG.debug("Got to slurm plugin teardown")

    def append_model(self, models):
        """Handled a model appended to this output."""
        if self.plugin_enabled:
            LOG.debug("Got to slurm plugin append_model.")

            # TODO: This plugin should probably work directly off of the
            # slurmdbd database schema. The flow of operations should go
            # something like this:
            #
            # * Gather a list of the users in slurmdbd (dbd_users_orig).
            # * Determine users to remove (dbd_users_remove).
            # * Determine users to add (dbd_users_add).
            # * Remove users from slurmdbd who shouldn't be there (sql).
            # * Add users who should be there (sql).
            # * Update the priorities of ALL users to keep things simple (sql).
            #
            # Notes:
            #
            # There should be an easy abstraction to handle different versions
            # of the slurmdbd schema to upgrade slurmdbd versions.
            #
            # There should be a safeguard so we don't delete or add a huge
            # number of users at once.

# EOF
