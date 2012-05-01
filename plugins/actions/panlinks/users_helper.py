#
# An action plugin for hypnotoad to create panasas links.
#

import sys
import os
import logging
import json
import re

sys.path.append(os.path.abspath('plugins/actions/panlinks'))

from hypnotoad import hypnofs
from base_classes import *

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
        """
        Create missing home directories under each realm for the users which
        have a datamodel entry, but do not have a disk entry.
        """
        LOG.debug("Creating missing home directories.")

        users_missing_homes = self.users_missing_homes( \
            disk_users, datamodel_users, realms)
        users_without_homes = self.users_in_this_not_that( \
            datamodel_users, disk_users)

        for u in users_without_homes:
            # Create a new directory on all realms.
            LOG.debug("Creating directory on all realms for user `" + k.short_name + "'.")
            for c in u.compartments:
                for r in realms:
                    self.create_home(u, r, c)

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
        if len(r.failures) > 0:
            LOG.debug("Skipping home creation on realm `" + r.base_name + \
                "' since we might have an incomplete volume listing.")
            return

        volume_set = None
        for c in realm.compartments:
            if c.short_name == compartment.short_name:
                volume_set = c.volumes
        if not volume_set:
            LOG.error("Attempted to create a home on a realm without" +
                " the correct compartment.")
            return
        volume_to_use = self.get_volume_with_least_users(volume_set)

        #LOG.debug("Home creation volume set is " + str([v.absolute_path for v in volume_set]) + ".")
        #LOG.debug("Volume with least users is `" + volume_to_use.absolute_path + "'.")

        full_path = os.path.join(volume_to_use.absolute_path, user.short_name)
        LOG.info("Creating a user home for `" + \
            user.short_name + "' at `" + full_path + "'.")

        self.commit_home_to_disk(full_path, user)

    def commit_home_to_disk(self, path, user):
        """
        Perform the operations required to create a home directory on a realm
        where one does not currently exist.
        """  

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

        # Now lets verify the UID to make sure it's sane.
        if not isinstance(user.uid, int) or user.uid < 1:
            LOG.error("Attempted to chmod a new directory for user `" +
                user.short_name + "' with a uid of `" + user.uid + "'.")
            return

        # Check to see if a group name is specified, otherwise we'll default
        # to using the user name as the group name.
        try:
            group_name = config.get('Action Options', 'panlinks_new_dir_group')
        except ConfigParser.NoOptionError:
            group_name = user.uid

        # Now we can actually change the ownership.
        (_, failed) = FS.chown(path, user.uid, group_name, self.command_timeout)
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

    def create_convenience_symlinks(self, disk_users):
        """
        Create convienience symlinks. Convienience symlinks are symlinks
        which allow users to use their home space without needing to know
        know what volume in a realm they actually have a directory on.
        """

        # Check to see if the filesystem for convenience symlinks
        # is mounted.
        (result, failure) = FS.ismount( \
            self.convenience_mount_dir, self.command_timeout)
        if failure or not result:
            LOG.error("The mount point required for convenience symlinks " +
                "does not exist. We will not create convenience symlinks " +
                "on this run.")
            return

        root_symlinks_path = os.path.join( \
            self.convenience_mount_dir, self.convenience_subdir)
        LOG.debug("Using root path of `" + root_symlinks_path + \
            "' to create convenience symlinks.")

        # Lay out the directory structure.
        dir_layout = []
        for u in disk_users:
            for h in u.homes:
                c_name = h.compartment.short_name

                if self.compartment_options[c_name]['symlink_prefix']:
                    prefix = self.compartment_options[c_name]['symlink_prefix']:
                else:
                    prefix = ""

                dir_layout.append(prefix + h.realm.base_name)
        for base_name in set(dir_layout):
            layout_dir = os.path.join(root_symlinks_path, base_name)
            (_, failed) = FS.makedirs(layout_dir, self.command_timeout)
            if failed:
                LOG.error("Creation of a new user directory failed! TODO: Better reporting here.")
                return

        for u in disk_users:
            for h in u.homes:
                c_name = h.compartment.short_name
                if self.compartment_options[c_name]['symlink_prefix']:
                    prefix = self.compartment_options[c_name]['symlink_prefix']:
                else:
                    prefix = ""

                src_path = os.path.join(h.volume.absolute_path, u.short_name)
                dest_path = os.path.join( \
                    root_symlinks_path, prefix + h.realm.base_name, \
                    u.short_name)

                LOG.debug("Creating convenience symlink from `" + src_path + "' to `" + dest_path + "'.")
                self.commit_symlink_to_disk(src_path, dest_path)

        return

    def commit_symlink_to_disk(self, src_path, dest_path):
        """
        Perform the operations necessary to lay a symlink down onto disk.
        """
        (_, failed) = FS.symlink(src_path, dest_path, self.command_timeout)
        if failed:
            LOG.error("Could not create a symlink to `" + dest_path + "'.")
        return

    def users_missing_homes(self, disk_users, datamodel_users, realms):
        """
        Determine what users should have a home on the realms
        specified, but does not.
        """
        users = []
        all_compartments = {}

        andusers = self.users_in_this_and_that( \
            disk_users, datamodel_users)

        # Gather all compartments in use.
        for realm in realms:
            for u in andusers:
                # This MUST be the user object from the datamodel or homes on
                # new compartments will not be created.
                for c in u.compartments:
                    has_home_here = False
                    for h in u.homes:
                        if h.realm.base_name == realm.base_name:
                            if h.compartment.short_name == c.short_name:
                                has_home_here = True
                    if not has_home_here:
                        LOG.debug("User `" + u.short_name + \
                            "' is missing a home on `" + realm.base_name + \
                            "' in compartment `" + c.short_name + "'.")
                        users.append((u,realm,c))
        
        # Debug
        #self.dump_user_info(users)
        return users

    def users_in_this_and_that(self, this, that):
        """
        Determine the users in this list and that list. Returns a list
        of objects pointing to this objects.
        """
        users = []
        that_hash = {}
        for u in that:
            that_hash[u.short_name] = 1
        for u in this:
            if u.short_name in that_hash:
                users.append(u)
        return users

    def users_in_this_not_that(self, this, that):
        """
        Determine the users in this list, but not that list. Returns
        a list of objects pointing to this objects.
        """
        users = []
        that_hash = {}
        for u in that:
            that_hash[u.short_name] = 1
        for u in this:
            if not u.short_name in that_hash:
                users.append(u)
        return users

# EOF
