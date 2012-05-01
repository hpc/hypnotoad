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

class FileSystemHelper():

    def __init__(self, config):
        self.new_dir_perms = config.get('Action Options', 'panlinks_new_dir_perms')
        self.command_timeout = config.getint('Action Options', 'panlinks_subprocess_timeout')

        # How to tell what volumes match up to each compartment. As well as
        # overrides for specifying a compartment for an entire realm.
        compartment_options_json = config.get('Action Options', 'panlinks_compartment_options')
        self.compartment_options = json.loads(compartment_options_json)

        # Cache the compartment matchers for volumes and realms.
        for c, opts in self.compartment_options.iteritems():

            if opts['vol_regex']:
                self.compartment_options[c]['volume_matcher'] = re.compile(opts['vol_regex'])
                LOG.debug("Compartment `" + str(c) + \
                    "' using volume regex `" + opts['vol_regex'] +
                    "' with symlink prefix `" + str(opts['symlink_prefix']) + "'.")

            if opts['realm_regex']:
                self.compartment_options[c]['realm_matcher'] = re.compile(opts['realm_regex'])
                LOG.debug("Compartment `" + str(c) + \
                    "' using realm regex `" + opts['realm_regex'])
                    "' with symlink prefix `" + str(opts['symlink_prefix']) + "'.")

    def gather_users_from_realms(self, realms):
        """
        This combines the users list from each realm to form a list of unique
        users that is cleaner than the combined realm lists.
        """
        raw_users = []
        user_dict = {}

        for r in realms:
            for c in r.compartments:
                for v in c.volumes:
                    for u in v.users:
                        raw_users.append(u)

        for u in raw_users:
            if u.short_name in user_dict:
                user_dict[u.short_name].homes = \
                    user_dict[u.short_name].homes + (u.homes)
            else:
                user_dict[u.short_name] = u

            homes_dict = {}
            for h in user_dict[u.short_name].homes:
                if not h.absolute_path in homes_dict:
                    homes_dict[h.absolute_path] = h

            user_dict[u.short_name].homes = homes_dict.values()

        return [v for k,v in user_dict.items()]

    def gather_realm_info(self, mount_points):
        """
        Create realm objects from mount point information. Realm objects
        contain basic information on the contents of each scratch space.
        """
        realms = []

        for m in mount_points:
            absolute_path = os.path.normpath(m)
            base_name = os.path.basename(absolute_path)
            containing_path = absolute_path[:len(base_name)-1]

            realm = ScratchRealm(base_name)
            realm.absolute_path = absolute_path
            realm.containing_path = containing_path

            realm.compartments = realm.compartments + self.gather_compartment_info(realm)

            realms.append(realm)
            
        return realms

    def gather_compartment_info(self, realm):
        """
        Create compartment objects from realm information. Compartment objects
        specify which volumes are included in a compartment.
        """
        LOG.info("Gathering compartments for realm `" + realm.base_name + "'.")
        compartments = []

        volume_names, failed_to_list = FS.listdir(realm.absolute_path)
        if failed_to_list:
            realm.failures.append(ScratchFailure("Failed to list any volumes."))
            return compartments
        LOG.debug("Volume list: `" + str(volume_names) + "'.")

        # If a realm matcher isn't specified, base the compartment on
        # the volume.
        for compartment_name in self.compartment_options.iterkeys():

                compartment = ScratchCompartment(compartment_name)

                # Check to see if every volume in this realm should be in
                # the new compartment. Realm matchers override volume
                # matchers.
                if self.compartment_options[compartment_name]['realm_matcher']:
                    realm_matcher = self.compartment_options[compartment_name]['realm_matcher']
                    if realm_matcher.match(realm.base_name):
                        for volume_name in volume_names:
                            volume = self.gather_volume_info(volume_name, realm, compartment)
                            compartment.volumes.append(volume)

                            #LOG.debug("Using realm matcher, " + \
                            #    "placed volume `" + volume_name + \
                            #    "' on realm `" + realm.base_name + \
                            #    "' into compartment `" + compartment_name + "'.")

                # Check to see if only specific volumes in this realm should
                # be in the new compartment.
                elif self.compartment_options[compartment_name]['volume_matcher']:
                    vol_matcher = self.compartment_options[compartment_name]['volume_matcher']

                    for volume_name in volume_names:
                        if vol_matcher.match(volume_name):
                            volume = self.gather_volume_info(volume_name, realm, compartment)
                            compartment.volumes.append(volume)

                            #LOG.debug("Using volume matcher, " + \
                            #    "placed volume `" + volume_name + \
                            #    "' on realm `" + realm.base_name + \
                            #    "' into compartment `" + compartment_name + "'.")

                # Add this new compartment into the total.
                if len(compartment.volumes) > 0:
                    compartments.append(compartment)

        return compartments

    def gather_volume_info(self, name, realm, compartment):
        volume = ScratchVolume(name, realm, compartment)
        volume.absolute_path = os.path.join(realm.absolute_path, name)

        user_names, failed_to_list = FS.listdir(volume.absolute_path)
        if failed_to_list:
            realm.failures.append( \
                ScratchFailure("Failed to list volume `" + \
                volume.absolute_path + "'."))
        for user_name in user_names:
            user = self.gather_user_info(user_name, realm, compartment, volume)
            volume.users.append(user)

        return volume

    def gather_user_info(self, name, realm, compartment, volume):
        user = ScratchUser(name)

        home = ScratchHome(realm, volume, compartment, user)
        home.absolute_path = os.path.join( \
            realm.absolute_path, volume.base_name, user.short_name)

        user.volumes.append(volume)
        user.compartments.append(compartment)
        user.homes.append(home)

        return user

# EOF
