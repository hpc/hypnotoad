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

class HomesHelper():

    def __init__(self, config):
        self.config = config

    def create_missing_homes(self, disk_users, datamodel_users):

    def get_volume_with_least_users(self, volumes):
        """
        Determines the volume in a realm with the least number of users and
        returns the name.
        """
        return volumes.sort(key=lambda v: len(v.users))[0] if volumes else None

    def create_convenience_symlinks(self, datamodel_users)

# EOF
