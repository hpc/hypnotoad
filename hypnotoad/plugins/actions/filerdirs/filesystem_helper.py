#
# An action plugin for hypnotoad to create filer dirs.
#

import sys
import os
import logging
import re

try:
    import json
except ImportError, e:
    import simplejson as json

sys.path.append(os.path.abspath('plugins/actions/filerdirs'))

from hypnotoad.core import hypnofs
from base_classes import *

LOG = logging.getLogger('root')
FS = hypnofs.hypnofs()

class FileSystemHelper():

    def __init__(self, config):
        self.new_dir_perms = config.get('Action Options', 'filerdirs_new_dir_perms')
        self.command_timeout = config.getint('Action Options', 'filerdirs_subprocess_timeout')

        # How to tell what volumes match up to each compartment. As well as
        # overrides for specifying a compartment for an entire realm.
        compartment_options_json = config.get('Action Options', 'filerdirs_compartment_opts')
        self.compartment_options = json.loads(compartment_options_json)

        # Cache the compartment matchers for volumes and realms.
        for c, opts in self.compartment_options.iteritems():
            for rx in opts['realm_regex']:
                self.compartment_options[c]['realm_matcher'] = re.compile(rx)
                LOG.debug("Compartment `" + str(c) +
                    "' using realm regex `" + str(rx) + "'.")

    def gather_users_from_realms(self, realms):
        """
        This combines the users list from each realm to form a list of unique
        users that is cleaner than the combined realm lists.
        """
        raw_users = []
        user_dict = {}

        for r in realms:
            for u in r.users:
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
                    homes_dict[h] = h

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

            self.gather_users_in_realm(realm)
            realms.append(realm)
            
        return realms

    def gather_compartment_info(self, realm):
        """
        Create compartment objects from realm information. Compartment objects
        specify which realms are included in a compartment.
        """
        LOG.debug("Gathering compartments for realm `" + realm.base_name + "'.")
        compartments = []

        # If a realm matcher isn't specified, base the compartment on
        # the volume.
        for compartment_name in self.compartment_options.iterkeys():

            compartment = ScratchCompartment(compartment_name)

            # Check to see if every volume in this realm should be in
            # the new compartment. Realm matchers override volume
            # matchers.
            if 'realm_matcher' in self.compartment_options[compartment_name]:
                realm_matcher = self.compartment_options[compartment_name]['realm_matcher']
                if realm_matcher.match(realm.base_name):
                    compartment.realms.append(realm)

                    LOG.debug("Using realm matcher, " + \
                        " placed realm `" + realm.base_name + \
                        "' into compartment `" + compartment_name + "'.")

                    compartments.append(compartment)

        LOG.debug("Found compartments `" + str(compartments) + "'.")
        return compartments

    def gather_users_in_realm(self, realm):
        """
        Gather information on users within a realm.
        """
	user_names, failed_to_list = FS.listdir(realm.absolute_path)
        LOG.debug("Users listed in realm `" + str(realm.base_name) + "': " + str(user_names))

        if failed_to_list:
            realm.failures.append( \
                ScratchFailure("Failed to list realm `" + \
                realm.absolute_path + "'."))
            return
        for user_name in user_names:
            user = ScratchUser(user_name)

            home = ScratchHome(realm, None, user)
            home.absolute_path = os.path.join( \
                realm.absolute_path, user.short_name)

            user.homes.append(home)
            realm.users.append(user)

# EOF
