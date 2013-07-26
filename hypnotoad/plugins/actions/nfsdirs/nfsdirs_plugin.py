#
# An action plugin for hypnotoad to create filer dirs for new users
#

import logging
import os
import sys

sys.path.append(os.path.abspath('plugins/actions/filerdirs'))

from hypnotoad.core import plugin
from setup_helper import *
from failure_helper import *
from filesystem_helper import *
from report_helper import *

LOG = logging.getLogger('root')

class filerdirs_plugin(plugin.action_plugin):
    def setup(self, config, model_version):
        """Called before the plugin is asked to do anything."""
        if config.getboolean('Action Options', 'filerdirs_plugin_enabled'):
            self.plugin_enabled = True
            LOG.debug("Filer Dirs plugin enabled")

            self.config = config
            self.model_version = model_version
        else:
            self.plugin_enabled = False

    def teardown(self):
        """Called to allow the plugin to free anything."""
        if self.plugin_enabled:
            LOG.debug("Got to Filer Dirs plugin teardown")

    def append_model(self, models):
        """Handle a model appended to this output."""
        if self.plugin_enabled:
            LOG.debug("Got to Filer Dirs plugin append_model.")

            # Perform basic sanity checks.
            setup_helper = SetupHelper(self.config)
            setup_helper.state_cache_update(models)
            realm_mount_points = setup_helper.find_mount_points()

            # Gather information on what's currently in the filesystem.
            fs_helper = FileSystemHelper(self.config)
            realms = fs_helper.gather_realm_info(realm_mount_points)

            # Get info for users from our disk and datamodel (ldap).
            disk_users = fs_helper.gather_users_from_realms(realms)
            datamodel_users = setup_helper.collect_users(models)

            # Check to see if we've exceeded a failure limit so we can stop
            # before attempting to modify the disk.
            FailureHelper(self.config).check(realms)

            # Print out a report of the existing state.
            report_helper = ReportHelper(self.config)
            report_helper.print_summary(datamodel_users, disk_users, realms)

            # Attempt to create home directories where none exist.
            users_helper = UsersHelper(self.config)
            users_helper.create_missing_homes(disk_users, datamodel_users, realms)

# EOF
