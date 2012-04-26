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

class ReportHelper():

    def __init__(self, config):
        self.config = config

    def print_summary(self, datamodel_users, disk_users, realms):
        LOG.info("Found `" + str(len(datamodel_users)) + \
            "' users in the datamodel (ldap).")
        LOG.info("Found `" + str(len(disk_users)) + \
            "' users with entries on disk.")

        with_datamodel_no_disk = self.users_in_this_not_that( \
            datamodel_users, disk_users)
        with_disk_no_datamodel = self.users_in_this_not_that( \
            disk_users, datamodel_users)

        users_missing_homes = self.users_missing_homes(disk_users, datamodel_users, realms)

        LOG.info("Found `" + str(len(with_datamodel_no_disk)) + \
            "' users with datamodel (ldap) entries, but no entries on disk.")
        LOG.info("Found `" + str(len(users_missing_homes)) + \
            "' users with datamodel (ldap) entries, but some entries on disk.")
        LOG.info("Found `" + str(len(with_disk_no_datamodel)) + \
            "' users entries on disk, but no datamodel (ldap) entries.")
        LOG.info("Listing users on disk, but no datamodel (ldap) entry: `" + \
            str([u.short_name for u in with_disk_no_datamodel]))

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

    def dump_user_info(self, users):
        for u in users:
            LOG.info("User: `" + u.short_name + "'")
            for h in u.homes:
                LOG.info("\tHome (`" + h.compartment.short_name + "'): `" + \
                    h.realm.base_name + "'")

    def dump_realm_info(self, realms):
        for r in realms:
            LOG.info("Realm: `" + r.base_name + "'")
            for c in r.compartments:
                LOG.info("\tCompartment: `" + c.short_name + "'")
                for v in c.volumes:
                    LOG.info("\t\tVolume: `" + v.base_name + "'")
                    for u in v.users:
                        LOG.info("\t\t\tUser: `" + u.short_name + "'")
                        for h in u.homes:
                            LOG.info("\t\t\t\tHome: `" + h.realm.base_name + "'")

# EOF
