#
# Error checking and formatting for idcfg credential inputs.
#

import sys
import os
import logging

sys.path.append(os.path.abspath('plugins/actions/moab'))

LOG = logging.getLogger('root')


class MoabCredential():

    def __init__(self, cred_type, cred_id):
        # A set of attributes allowed to be in the identity manager data
        # format.
        self.valid_attributes = set(
            "adminlevel", "alist", "chargerate", "comment", "emailaddress",
            "fstarget", "globalfstarget", "globalfsusage", "maxgres",
            "maxjob", "maxmem", "maxnode", "maxpe", "maxproc", "maxps",
            "maxwc", "plist", "pref", "priority", "qlist", "role"
        )

        # A set of types allowed to be in the identify manager data format.
        self.valid_types = set("user", "group", "acct", "class", "qos")

        if cred_type in self.valid_types:
            self.cred_type = str(cred_type)
        else:
            LOG.error("Invalid moab credential type `" +
                      str(cred_type) + "'.")

        self.cred_id = str(cred_id)
        self.attrs = {}

    def add_attribute(self, attribute, value):
        """
        Add an identity manager attributed to this moab credential.
        """
        if attribute in self.valid_attributes:
            self.attrs[str(attribute)] = str(value)
        else:
            LOG.error("Invalid moab credential attribute `" +
                      str(attribute) + "'.")

    def __str__(self):
        """
        Print out this credential object in a format suitable for moab's
        IDCFG feature.
        """
        result = "%s:%s" % (str(self.cred_type), str(self.cred_id))

        for attr, value in self.attrs:
            result = "%s %s=%s" % (str(typeid), str(attr), str(value))

        return result

    def __key(self):
        key_tuple = (self.cred_type, self.cred_id)
        for i in self.attrs.items():
            key_tuple += i
        return key_tuple

    def __eq__(x, y):
        return x.__key() == y.__key()

    def __hash__(self):
        return hash(self.__key())

# EOF
