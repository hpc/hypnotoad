#
# An action plugin for hypnotoad to create panasas links.
#

import sys
import os
import logging
import json
import re

sys.path.append(os.path.abspath('plugins/actions/panlinks'))

from base_classes import *

LOG = logging.getLogger('root')

class UsersHelper():

    def __init__(self, config):
        self.config = config

    def create_missing_homes(self, disk_users, datamodel_users, realms):
        LOG.debug("Creating missing home directories.")

        for u in datamodel_users:
            if u.short_name not in [x.short_name for x in disk_users]:
                LOG.debug("User `" + u.short_name + \
                    "' needs a home on all realms.")
                self.create_home_on_realms(realms, u)
            else:
                for r in realms:
                    if not u.volumes.realm.short_name in [y.short_name for y in realms]:
                        LOG.debug("User `" + u.short_name + "' is missing a home on realm `" + r.short_name + "'.")
                        self.create_home_on_realms([r], u)

    def create_home_on_realms(realms, user):
        # TODO
        return

    def get_volume_with_least_users(self, volumes):
        """
        Determines the volume in a realm with the least number of users and
        returns the name.
        """
        return volumes.sort(key=lambda v: len(v.users))[0] if volumes else None

    def create_convenience_symlinks(self, datamodel_users):
        #TODO
        return

    def users_missing_homes(self, disk_users, datamodel_users, realms):
        users = {}
        all_compartments = {}

        andusers = self.users_in_this_and_that( \
            disk_users, datamodel_users)

        # Gather all compartments in use.
        for realm in realms:
            for u in andusers:
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
                        users.setdefault(ScratchCompartment, []).append(c)
        
        # Debug
        #self.dump_user_info(users)

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
