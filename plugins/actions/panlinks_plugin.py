#
# A action plugin for hypnotoad to create panasas links.
#

import os
import errno
import logging
import json
import pprint

from hypnotoad import plugin

LOG = logging.getLogger('root')
PP = pprint.PrettyPrinter(indent=4)

class panlinks_plugin(plugin.action_plugin):
    def setup(self, config, model_version):
        """Called before the plugin is asked to do anything."""
        if config.getboolean('Action Options', 'panlinks_plugin_enabled'):
            self.plugin_enabled = True
            LOG.debug("Panasas Links plugin enabled")

            self.state_dir = config.get('Basic Options', 'state_dir') + "/panlinks"
            self.new_dir_perms = config.getint('Action Options', 'panlinks_new_dir_perms')

            self.skip_bad_realms = config.getboolean('Action Options', 'panlinks_skip_bad_realms')
            self.max_diff_count = config.getint('Action Options', 'panlinks_max_diff_count')
            self.max_skip_bad_vols = config.getint('Action Options', 'panlinks_max_skip_bad_vols')
            self.max_skip_bad_realms = config.getint('Action Options', 'panlinks_max_skip_bad_realms')

            self.config = config
            self.model_version = model_version
        else:
            self.plugin_enabled = False

    def teardown(self):
        """Called to allow the plugin to free anything."""
        if self.plugin_enabled:
            LOG.debug("Got to Panasas Links plugin teardown")

    def append_model(self, models):
        """Handled a model appended to this output."""
        if self.plugin_enabled:
            LOG.debug("Got to Panasas Links plugin append_model.")
            self.create_links(models)

    def create_links(self, models):
        """Check everything and create the links."""

        self.cache_check_and_update(models)
        all_usernames = self.collect_users_from_models(models)

        mounted_panfs_list = get_current_panfs_mounts()
        users_with_existing_directories = get_users_with_existing_directories(mounted_panfs_list, all_usernames)

        if self.validate_existing_directories(all_usernames, users_with_existing_directories):
            for user in all_usernames - users_with_existing_directories:
                #user_dir_path = ???
                #self.ensure_dir(user_dir_path)
                raise NotImplementedError
            self.create_symlinks_for_valid_users(all_usernames, users_with_existing_directories)

    def collect_users_from_models(self, models):
        """ Merge all hypnotoad models into a single list of user names."""
        userlist = []
        for plug_model in models:
            for m in plug_model:
                if 'user_entry' in m.keys():
                    user = m['user_entry']
                    userlist.append(user['short_name_string'].strip())
        return userlist

    def get_users_with_existing_directories(self, mounts, userlist):
        """Find valid users that already have directories created."""
        dirlist = []
        for mount in mounts:
            for file in os.listdir(mount):
                """
                FIXME: handle vols.
                """
                if os.path.isdir(file):
                    dirlist.append(file)
        intersection = userlist & dirlist
        return intersection

    def cache_check_and_update(self, models):
        """
        If a cache exists, check differences and update the cache if the
        differences are not too great. Otherwise quietly create a cache if one
        does not exist already.
        """
        cache_file_name = self.state_dir + "/" + "model.json"
        self.ensure_dir(self.state_dir)

        def save_as_json(obj, dest_file_name):
            """Serializes obj to json and saves to a file at dest."""
            j = json.dumps(obj)
            f = open(dest_file_name, 'w')
            f.write(j + "\n")
            f.close()

        def json_to_models(json_file_name):
            f = open(json_file_name)
            return json.load(f)

        if os.path.isfile(cache_file_name):
            old_models = json_to_models(cache_file_name)

            old_userlist, new_userlist = map(self.collect_users_from_models, [old_models, models])
            model_diff_count = return len(list(set(old_userlist) - set(new_userlist)))

            if model_diff_count > self.max_diff_count:
                LOG.error("Model too different with " + model_diff_count + " changes.")
                raise UserWarning
            else:
                # Overwrite the old cache.
                save_as_json(models, cache_file_name)
        else:
            # Create a new cache if one does not exist.
            save_as_json(models, cache_file_name)

    def ensure_dir(self, path):
        """Create directory at path if it doesn't exist."""
        try:
            os.makedirs(path)
        except OSError as exc:
            if exc.errno == errno.EEXIST:
                pass
            else:
                raise

    def get_current_panfs_mounts(self):
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
                if l.find('panfs') != -1:
                    m.append(l.split()[1])
            return m

        fstab_mounts, mtab_mounts = map(tab_check, [open('/etc/fstab'), open('/etc/mtab')])
        if(fstab_mounts & mtab_mounts) == len(fstab_mounts):
            LOG.debug('All detected PanFS mounts are mounted.')
        else:
            LOG.warn('There are panfs mounts that are NOT mounted.')
        return mtab_mounts

# EOF
