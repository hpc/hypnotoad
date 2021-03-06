#
# A helper for printing out reports for the panlinks plugin.
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

from base_classes import *
from users_helper import *

LOG = logging.getLogger('root')


class ReportHelper():

    def __init__(self, config):
        self.config = config
        self.users_helper = UsersHelper(self.config)

    def print_summary(self, datamodel_users, disk_users, realms):
        """
        Print a summary of what was found when analyzing the realms.
        """
        LOG.info("Found `" + str(len(datamodel_users)) +
                 "' users in the datamodel (ldap).")
        LOG.info("Found `" + str(len(disk_users)) +
                 "' users with entries on disk.")

        with_datamodel_no_disk = self.users_helper.users_in_this_not_that(
            datamodel_users, disk_users)
        with_disk_no_datamodel = self.users_helper.users_in_this_not_that(
            disk_users, datamodel_users)
        users_missing_homes = self.users_helper.users_missing_homes(
            disk_users, datamodel_users, realms)

        LOG.info("Found `" + str(len(with_datamodel_no_disk)) +
                 "' users with datamodel (ldap) entries, but no entries on disk.")
        LOG.info("Found `" + str(len(users_missing_homes)) +
                 "' users with datamodel (ldap) entries, but some entries on disk.")
        LOG.info("Listing users with datamodel (ldap) entry, but some entries on disk: `" +
                 str([u.short_name for (u, r, c) in users_missing_homes]) + "'.")
        LOG.info("Found `" + str(len(with_disk_no_datamodel)) +
                 "' objects on disk that have no datamodel (ldap) entry.")
        LOG.info("Listing objects on disk that have no datamodel (ldap) entry: `" +
                 str([u.short_name for u in with_disk_no_datamodel]))

    def dump_user_volume_list(self, realms):
        """
        Dump a list of volumes and the users with homes in them. The output of
        this should be suitable for splunk.
        """
        output = []
        for r in realms:
            realm = {str(r.base_name): []}
            for c in r.compartments:
                for v in c.volumes:
                    volume = {str(v.base_name): []}
                    for u in v.users:
                        volume[str(v.base_name)].append(u.short_name)
                    realm[str(r.base_name)].append(volume)
            output.append(realm)
        LOG.info("Scratch-Volume-User: " + json.dumps(output))

    def dump_user_info(self, users):
        """
        Dump basic information on each user in the array of users. Useful
        for debugging.
        """
        for u in users:
            LOG.info("User: `" + u.short_name + "'")
            for h in u.homes:
                LOG.info("\tHome (`" + h.compartment.short_name + "'): `" +
                         h.realm.base_name + "'")

    def dump_realm_info(self, realms):
        """
        Dump basic information on each realm in the array of realms. Useful
        for debugging.
        """
        for r in realms:
            LOG.info("Realm: `" + r.base_name + "'")
            for c in r.compartments:
                LOG.info("\tCompartment: `" + c.short_name + "'")
                for v in c.volumes:
                    LOG.info("\t\tVolume: `" + v.base_name + "'")
                    for u in v.users:
                        LOG.info("\t\t\tUser: `" + u.short_name + "'")
                        for h in u.homes:
                            LOG.info("\t\t\t\tHome: `" +
                                     h.realm.base_name + "'")

# EOF
