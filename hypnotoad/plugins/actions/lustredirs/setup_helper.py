#
# Helpers related to setup.
#

import logging
import os
import sys
import shlex

try:
    import json
except ImportError, e:
    import simplejson as json

sys.path.append(os.path.abspath('plugins/actions/lustredirs'))

from hypnotoad.core import hypnofs
from base_classes import *

LOG = logging.getLogger('root')
FS = hypnofs.hypnofs()

class SetupHelper():

    def __init__(self, config):
        self.state_dir = config.get('Basic Options', 'state_dir') + "/lustredirs"
        self.max_diff_count = config.getint('Action Options', 'lustredirs_max_diff_count')

        # The realm skip list is comma seperated.
        self.realms_to_skip = shlex.shlex(config.get('Action Options', 'lustredirs_skip_realms'))
        self.realms_to_skip.whitespace += ','
        self.realms_to_skip.whitespace_split = True

    def collect_users(self, models):
        """ Merge all hypnotoad models into a single array of ScratchUsers."""
        users = []
        for plug_model in models:
            for m in plug_model:
                if 'user_entry' in m.keys():
                    user_model = m['user_entry']
                    user = ScratchUser(user_model['short_name_string'], \
                        user_model['user_id_integer'], \
                        user_model['group_id_integer'])
                    for c in user_model['compartment_access_array']:
                        #LOG.debug("Model, adding compartment `" + c + "` " + \
                        #    "to user `" + user.short_name + "`.")
                        user.compartments.append(ScratchCompartment(c))

                    users.append(user)
        return users

    def state_cache_update(self, models):
        """
        If a cache exists, check differences and update the cache if the
        differences are not too great. Otherwise quietly create a cache if one
        does not exist already.
        """
        cache_file_name = self.state_dir + "/" + "model.json"
        if FS.makedirs(self.state_dir)[1] is True:
            LOG.error("Could not create a state directory at `" + self.state_dir + "'.")
            sys.exit()

        def save_as_json(obj, dest_file_name):
            """Serializes obj to json and saves to a file at dest."""
            LOG.debug("Saving to json at: " + dest_file_name)
            j = json.dumps(obj)
            f = open(dest_file_name, 'w')
            f.write(j + "\n")
            f.close()

        def json_to_models(json_file_name):
            LOG.debug("Reading in json file at: " + json_file_name)
            f = open(json_file_name)
            return json.load(f)

        if FS.isfile(cache_file_name) is (False, False):
            old_models = json_to_models(cache_file_name)

            old_userlist, new_userlist = map(self.collect_users, [old_models, models])
            model_diff_count = len(list(set(old_userlist) - set(new_userlist)))

            if model_diff_count > self.max_diff_count:
                LOG.error("Too many objects in the model (ldap) have changed." + \
                    "Since the number of differences `" + str(model_diff_count) + \
                    "' is greater than the configuration limit of `" + \
                    str(self.max_diff_count) + "', we'll exit now. " +
                    "If this is intended, please change the model difference limit " + \
                    "in the configuration or remove the panlinks model cache " +
                    " at `" + str(cache_file_name) + "' so it can be automatically recreated.")
                raise UserWarning
            else:
                # Overwrite the old cache.
                LOG.debug("Verified existing model as sane. We can safely continue.")
                save_as_json(models, cache_file_name)
        else:
            # Create a new cache if one does not exist.
            save_as_json(models, cache_file_name)

    def find_mount_points(self):
        """
        Check if all panfs mounts specified in fstab are mounted. Display a
        warning if not. Return mounted panfs mount points.
        """
        def tab_check(f):
            m = []
            for l in f.readlines():
                i = l.find('#')
                if i != -1:
                    l = l[:i]
                    l = l.rstrip()
                if l.find('type lustre') != -1:
                    m.append(l.split()[1])
            return set(m)

        fstab_mounts, mtab_mounts = map(tab_check, [open('/etc/fstab'), open('/etc/mtab')])
        if len(fstab_mounts & mtab_mounts) == len(fstab_mounts):
            LOG.info('All detected lustre mounts are mounted.')
        else:
            LOG.warning('There are lustre mounts that are NOT mounted.')

        skips = list(self.realms_to_skip)
        for s in skips:
            LOG.debug("Configuration requires skipping realm: '" + str(s) + "'.")
            mtab_mounts.discard(s)

        LOG.info("Using realm mount points: " + str(mtab_mounts))
        return mtab_mounts

# EOF
