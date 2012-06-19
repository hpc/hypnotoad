#
# An action plugin for hypnotoad to create panasas links.
#

import sys
import os
import logging
import re

try:
    import json
except ImportError, e:
    import simplejson as json

sys.path.append(os.path.abspath('plugins/actions/panlinks'))

from hypnotoad.core import hypnofs
from base_classes import *
from report_helper import *

LOG = logging.getLogger('root')
FS = hypnofs.hypnofs()

class UsersHelper():

    def __init__(self, config):
        self.config = config

        self.new_dir_perms = config.get('Action Options', 'panlinks_new_dir_perms')
        self.command_timeout = config.getint('Action Options', 'panlinks_subprocess_timeout')

        self.convenience_mount_dir = config.get('Action Options', 'panlinks_convenience_mount')
        self.convenience_subdir = config.get('Action Options', 'panlinks_convenience_subdir')

        # To find convienence symlink prefixes for each compartment.
        compartment_options_json = config.get('Action Options', 'panlinks_compartment_options')
        self.compartment_options = json.loads(compartment_options_json)

    def create_missing_homes(self, disk_users, datamodel_users, realms):
        #LOG.debug("Creating missing home directories.")

        users_missing_homes = self.users_missing_homes( \
            disk_users, datamodel_users, realms)

        for u,r,c in users_missing_homes:
            LOG.debug("Creating new directory for user `" + \
                str((u.short_name,r.base_name,c.short_name)) + "'.")
            self.create_home(u, r, c)

    def create_home(self, user, realm, compartment):
        """
        Create a new home directory by first finding the correct volume
        set for the compartment, then by finding what volume in the
        volume set has the least number of users.
        """
        volume_set = None

        if realm.has_failed:
            LOG.error("Detected failures on realm `" + realm.base_name + \
                "'. Skipping creation of new user directory for `" + \
                user.short_name + "'.")
            return

        for c in realm.compartments:
            if c.short_name == compartment.short_name:
                volume_set = c.volumes
        if not volume_set:
            LOG.error("Attempted to create a home on a realm without" +
                " the correct compartment.")
            return
        volume_to_use = self.get_volume_with_least_users(volume_set)

        LOG.debug("Home creation volume set is " + str([v.absolute_path for v in volume_set]) + ".")
        LOG.debug("Volume with least users is `" + volume_to_use.absolute_path + "'.")

        full_path = os.path.join(volume_to_use.absolute_path, user.short_name)
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

    def get_volume_with_least_users(self, volumes):
        """
        Determines the volume in a realm with the least number of users and
        returns the name.
        """
        if volumes:
            return sorted(volumes, key=lambda v: len(v.users))[0]
        else:
            return None

    def create_convenience_symlinks(self, disk_users, datamodel_users):
        # Check to see if the filesystem for convenience symlinks
        # is mounted.
        (result, failure) = FS.ismount( \
            self.convenience_mount_dir, self.command_timeout)
        if failure or not result:
            LOG.error("The mount point required for convenience symlinks " +
                "does not exist. We will not create convenience symlinks " +
                "on this run.")
            return

        andusers = self.users_in_this_and_that( \
            disk_users, datamodel_users)

        root_symlinks_path = os.path.join( \
            self.convenience_mount_dir, self.convenience_subdir)
        LOG.debug("Using root path of `" + root_symlinks_path + \
            "' to create convenience symlinks.")

        # Lay out the directory structure.
        dir_layout = []
        for u in andusers:
            for h in u.homes:
                c_name = h.compartment.short_name

                if self.compartment_options[c_name]['symlink_prefix']:
                    prefix = self.compartment_options[c_name]['symlink_prefix']
                else:
                    prefix = ""

                dir_layout.append(prefix + h.realm.base_name)
        for base_name in set(dir_layout):
            layout_dir = os.path.join(root_symlinks_path, base_name)
            (_, failed) = FS.makedirs(layout_dir, self.command_timeout)
            if failed:
                LOG.error("Creation of a new user directory failed! TODO: Better reporting here.")
                return

        for u in andusers:
            for h in u.homes:
                c_name = h.compartment.short_name
                prefix = self.compartment_options[c_name]['symlink_prefix']

                src_path = os.path.join(h.volume.absolute_path, u.short_name)
                dest_path = os.path.join( \
                    root_symlinks_path, prefix + h.realm.base_name, \
                    u.short_name)

                #LOG.debug("Creating convenience symlink from `" + src_path + "' to `" + dest_path + "'.")
                self.commit_symlink_to_disk(src_path, dest_path)

        return

    def commit_symlink_to_disk(self, src_path, dest_path):
        (_, failed) = FS.symlink(src_path, dest_path, self.command_timeout)
        if failed:
            LOG.error("Could not create a symlink to `" + dest_path + "'.")
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
            for compartment in realm.compartments:
                # Use the datamodel for the most complete list.
                for datamodel_user in datamodel_users:

                    # Assume the user doesn't have a home here until we find it
                    # in the datamodel.
                    user_should_have_home_here = False

                    # Assume the user doesn't have a home here until we find it
                    # on the disk.
                    user_has_home_here = False

                    # Find the cooresponding disk user for this datamodel user.
                    disk_user = next((disk_user for disk_user in disk_users if \
                        disk_user.short_name == datamodel_user.short_name), None)

                    # Now check the datamodel to see if the user should have a
                    # home here.
                    for datamodel_compartment in datamodel_user.compartments:
                        if datamodel_compartment.short_name == compartment.short_name:

                            LOG.debug("User `" + datamodel_user.short_name + \
                                "' SHOULD have a home on `" + realm.base_name + \
                                "' in compartment `" + compartment.short_name + "'.")

                            user_should_have_home_here = True

                    # Now check the disk to see if the user actually has a home here.
                    if disk_user:
                        #LOG.debug("User `" + datamodel_user.short_name + \
                        #    "' has homes on disk `" + str(disk_user.homes) + "'.")

                        for disk_home in disk_user.homes:
                            if disk_home.realm.base_name == realm.base_name:
                                if disk_home.compartment.short_name == compartment.short_name:

                                    LOG.debug("User `" + datamodel_user.short_name + \
                                        "' DOES have a home on `" + realm.base_name + \
                                        "' in compartment `" + compartment.short_name + "'.")

                                    user_has_home_here = True

                    if not user_has_home_here:
                        if user_should_have_home_here:
                            LOG.debug("User `" + datamodel_user.short_name + \
                                "' is MISSING a home on `" + realm.base_name + \
                                "' in compartment `" + compartment.short_name + "'.")
                            users.append((datamodel_user,realm,compartment))

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
