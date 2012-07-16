#
# An action plugin for hypnotoad to create lustre dirs.
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

LOG = logging.getLogger('root')
FS = hypnofs.hypnofs()

class FileSystemHelper():

    def __init__(self, config):
        self.new_dir_perms = config.get('Action Options', 'lustredirs_new_dir_perms')
        self.command_timeout = config.getint('Action Options', 'lustredirs_subprocess_timeout')

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

            self.gather_users_in_realm(realm)
            realms.append(realm)
            
        return realms

    def gather_users_in_realm(self, realm):
        """
        Gather information on users within a realm.
        """
	user_names, failed_to_list = FS.listdir(realm.absolute_path)
        if failed_to_list:
            realm.failures.append( \
                ScratchFailure("Failed to list realm `" + \
                realm.absolute_path + "'."))
            return
        for user_name in user_names:
            user = ScratchUser(user_name)

            home = ScratchHome(realm, user)
            home.absolute_path = os.path.join( \
                realm.absolute_path, user.short_name)

            user.homes.append(home)
            realm.users.append(user)

# EOF
