#
# An action plugin for hypnotoad to create lustre directories.
#

import sys
import os
import logging
import re

try:
    import json
except ImportError, e:
    import simplejson as json

sys.path.append(os.path.abspath('plugins/actions/lustredirs'))

from hypnotoad.core import hypnofs
from base_classes import *
from report_helper import *

LOG = logging.getLogger('root')
FS = hypnofs.hypnofs()

class UsersHelper():

    def __init__(self, config):
        self.config = config

        self.new_dir_perms = config.get('Action Options', 'lustredirs_new_dir_perms')
        self.command_timeout = config.getint('Action Options', 'lustredirs_subprocess_timeout')

    def create_missing_homes(self, disk_users, datamodel_users, realms):
        #LOG.debug("Creating missing home directories.")

        users_missing_homes = self.users_missing_homes( \
            disk_users, datamodel_users, realms)

        for u,r in users_missing_homes:
            LOG.debug("Creating new directory for user `" + \
                str((u.short_name,r.base_name)) + "'.")
            self.create_home(u, r)

    def create_home(self, user, realm):
        """
        Create a new home directory for the user on the realm specified.
        """
        if realm.has_failed:
            LOG.error("Detected failures on realm `" + realm.base_name + \
                "'. Skipping creation of new user directory for `" + \
                user.short_name + "'.")
            return

        full_path = os.path.join(realm.absolute_path, user.short_name)
        LOG.info("Creating a user home for `" + \
            user.short_name + "' at `" + full_path + "'.")

        self.commit_home_to_disk(full_path, user)

    def commit_home_to_disk(self, path, user):

        # Lets go ahead and actually create the directory
        (_, failed) = FS.makedirs(path, self.command_timeout)
        if failed:
            LOG.error("Creation of a new user directory failed! TODO: Better reporting here.")
            return

        # Now set the permissions
        (_, failed) = FS.chmod(path, self.new_dir_perms, self.command_timeout)
        if failed:
            LOG.error("Setting permissions on a new user directory failed! TODO: Better reporting here.")
            return

        # Now set the ownership
        (_, failed) = FS.chown(path, user.uid, user.gid, self.command_timeout)
        if failed:
            LOG.error("Setting ownership of a new user directory failed! TODO: Better reporting here.")
            return

        return

    def users_missing_homes(self, disk_users, datamodel_users, realms):
        """
        Find all users who are missing home directories.
        """
        users = []
        all_compartments = {}

        LOG.debug("Checking `" + str(len(datamodel_users)) + \
            "' users for missing home directories.")

        # Check to make sure a user has a home in each compartment in this
        # realm.
        for realm in realms:
            # Use the datamodel for the most complete list.
            for datamodel_user in datamodel_users:

                # Assume all users should have a home on lustre.
                user_should_have_home_here = True

                # Assume the user doesn't have a home here until we find it
                # on the disk.
                user_has_home_here = False

                # Find the cooresponding disk user for this datamodel user.
                disk_user = next((disk_user for disk_user in disk_users if \
                    disk_user.short_name == datamodel_user.short_name), None)

                # Now check the disk to see if the user actually has a home here.
                if disk_user:
                    LOG.debug("User `" + datamodel_user.short_name + \
                        "' has homes on disk `" + str(disk_user.homes) + "'.")

                    for disk_home in disk_user.homes:
                        if disk_home.realm.base_name == realm.base_name:

                            LOG.debug("User `" + datamodel_user.short_name + \
                                "' DOES have a home on `" + realm.base_name + "'.")

                            user_has_home_here = True

                if not user_has_home_here:
                    if user_should_have_home_here:
                        LOG.debug("User `" + datamodel_user.short_name + \
                            "' is MISSING a home on `" + realm.base_name + "'.")
                        users.append((datamodel_user,realm))

        # Debug
        #ReportHelper(self.config).dump_user_info(users)

        return users

    def users_in_this_and_that(self, this, that):
        users = []
        that_hash = {}
        for u in that:
            that_hash[u.short_name] = 1
        for u in this:
            if u.short_name in that_hash:
                users.append(u)
        return users

    def users_in_this_not_that(self, this, that):
        users = []
        that_hash = {}
        for u in that:
            that_hash[u.short_name] = 1
        for u in this:
            if not u.short_name in that_hash:
                users.append(u)
        return users

# EOF
