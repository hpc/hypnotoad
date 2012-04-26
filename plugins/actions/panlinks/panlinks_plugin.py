#
# An action plugin for hypnotoad to create panasas links.
#

import logging
import os
import sys

sys.path.append(os.path.abspath('plugins/actions/panlinks'))

from hypnotoad import plugin
from setup_helper import *
from failure_helper import *
from filesystem_helper import *
from report_helper import *

LOG = logging.getLogger('root')

class panlinks_plugin(plugin.action_plugin):
    def setup(self, config, model_version):
        """Called before the plugin is asked to do anything."""
        if config.getboolean('Action Options', 'panlinks_plugin_enabled'):
            self.plugin_enabled = True
            LOG.debug("Panasas Links plugin enabled")

            self.config = config
            self.model_version = model_version

            self.create_convenience = config.getboolean('Action Options', 'panlinks_convenience_create')
        else:
            self.plugin_enabled = False

    def teardown(self):
        """Called to allow the plugin to free anything."""
        if self.plugin_enabled:
            LOG.debug("Got to Panasas Links plugin teardown")

    def append_model(self, models):
        """Handled a model appended to this output."""
        if self.plugin_enabled:
            LOG.debug("Got to Panasas Links plugin append_model.")

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

            # For debugging
            #report_helper.dump_realm_info(realms)

            # Create the convenience symlinks. Note that a newly added user
            # will need to wait until the next time the panlinks script is
            # run before they have convienence symlinks added. This avoids
            # a second pass on the disk in a single run.
            users_helper = UsersHelper(self.config)
            if self.create_convenience:
                users_helper.create_convenience_symlinks(disk_users)

            # Attempt to create home directories where none exist.
            # perform symlink creation.
            users_helper.create_missing_homes(disk_users, datamodel_users, realms)

# EOF
