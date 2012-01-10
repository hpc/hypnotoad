#
# An action plugin for hypnotoad to create panasas links.
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
            self.new_dir_perms = config.get('Action Options', 'panlinks_new_dir_perms')

            self.root_mount_point = config.get('Action Options', 'panlinks_mount_point')

            self.skip_bad_realms = config.getboolean('Action Options', 'panlinks_skip_bad_realms')
            self.max_diff_count = config.getint('Action Options', 'panlinks_max_diff_count')
            self.max_skip_bad_vols = config.getint('Action Options', 'panlinks_max_skip_bad_vols')
            self.max_skip_bad_realms = config.getint('Action Options', 'panlinks_max_skip_bad_realms')

            self.create_pristine = config.getboolean('Action Options', 'panlinks_pristine_dir_create')
            self.pristine_mount_dir = config.get('Action Options', 'panlinks_pristine_mount_dir')
            self.pristine_subdir = config.get('Action Options', 'panlinks_pristine_subdir')

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

            self.cache_check_and_update(models)

            all_usernames = self.collect_users_from_models(models)
            self.ensure_user_directories_exist(all_usernames)

    def ensure_user_directories_exist(self, all_usernames):
        """
        Check to make sure each user has a directory located on a single
        volume on each realm. Then, ensure that a symlink exists for each
        realm.
        """
        mounted_panfs_list = self.get_current_panfs_mounts()

        users_with_orig_dirs, where_user_orig_dir_is = get_user_original_directory_info(mounted_panfs_list, all_usernames)
        users_without_orig_dirs = set(all_usernames) - set(users_with_existing_orig_dirs)

        LOG.debug("Users without directories: " + users_without_orig_dirs)
        if len(users_without_orig_dirs) > self.max_diff_count:
            LOG.debug("Too many missing users. We have " + len(all_usernames) + " total users, but only " + len(users_with_orig_dirs) + " have existing directories.")
            raise UserError

        """Create intial directories and symlinks for new users."""
        for user in users_without_orig_dirs:
            create_initial_directories_for(user, map(os.path.basename, mounted_panfs_list))

        """Just verify symlinks for users with existing directories."""
        for u in users_with_orig_dirs:
            user_realm = where_user_orig_dir_is[u].realm
            user_volume = where_user_orig_dir_is[u].volume
            self.ensure_symlink_for_user("/", u, user_realm, user_volume)

        """Go back and create a pristine directory if necessary."""
        if self.create_pristine:
            pristine_users, pristine_where = get_user_original_directory_info(mounted_panfs_list, all_usernames)
            for u in pristine_users:
                realm = where[u].realm
                volume = where[u].volume
                if os.path.ismount(self.pristine_mount_dir):
                    pristine_path = self.pristine_mount_dir + "/" + self.pristine_subdir
                    self.ensure_symlink_for_user(pristine_path, u, realm, volume)
                else:
                    LOG.debug("Pristine base path was not mounted.")
                    raise UserError

    def create_initial_directories_for(self, username, realms):
        """Create a new directory on each realm for the specified user."""
        for realm in realms:
            vol_name = self.get_volume_with_least_users(realm)
            user_dir_path = self.root_mount_point + "/" + realm + "/" + vol_name + "/" + username

            LOG.debug('Creating initial user directory "' + user_dir_path + '" for user "' + username)
            self.ensure_dir(user_dir_path)

            LOG.debug('Creating new symlink for user "' + username + '" on realm "' + realm + '".')
            self.ensure_symlink_for_user(username, realm, vol_name)

    def ensure_symlink_for_user(self, username, realm_name, volume_name, base):
        """
        Ensure that a symlink exists for the user in the specified location.
        """
        user_symlink_dst_path = base + realm_name + "/" + username
        user_symlink_src_path = self.root_mount_point + "/" + realm_name + "/" + volume_name + "/" + username
        
        if not os.path.exists(user_symlink_path):
            LOG.debug('Symlink missing at "' + user_symlink_path + '". Attempting to create.')
            os.symlink(user_symlink_src_path, user_symlink_dst_path)
            if not os.path.islink(user_symlink_dst_path):
                LOG.debug('Failed to create a symlink at: "' + user_symlink_dst_path + '".')

    def collect_users_from_models(self, models):
        """ Merge all hypnotoad models into a single list of user names."""
        userlist = []
        for plug_model in models:
            for m in plug_model:
                if 'user_entry' in m.keys():
                    user = m['user_entry']
                    userlist.append(user['short_name_string'].strip())
        return userlist

    def get_volume_with_least_users(self, realm):
        """
        Determines the volume in a realm with the least number of users and
        returns the name.
        """
        volume_with_least_users = None
        current_least_count = None
        realm_path = self.root_mount_point + "/" + realm

        if not os.path.isdir(realm_path):
            LOG.debug('The specified realm path "' + realm_path + '" does not exist.')
            raise UserError

        for volume_dir in os.listdir(realm_path):
            if not os.path.isdir(volume_dir):
                LOG.debug('Found a volume that is not a directory (' + volume_dir + ').')
                raise UserError
            users_in_this_volume = len(os.listdir(volume_dir))
            if current_least_count is None or users_in_this_volume < current_least_count:
                volume_with_least_users = volume_dir
                current_top_count = users_in_this_volume

        if volume_with_least_users is None:
            LOG.debug("Could not find a volume with the least number of users.")
            raise UserError

        return volume_with_least_users

    def get_user_original_directory_info(self, mounts, all_users):
        """
        Find valid users which already have directories created, as well as
        what volume users have directories on.
        """
        users_on_realm_vols = {}
        users_with_dirs = []

        for mount_dir in mounts:
            if not os.path.isdir(mount_dir):
                LOG.debug('Mount directory "' + mount_dir + '" is invalid.')
                raise UserError
            for volume_dir in os.listdir(mount_dir):
                if not os.path.isdir(volume_dir):
                    LOG.debug('Volume directory "' + volume_dir + '" is invalid.')
                    raise UserError
                for user_dir in os.listdir(volume_dir):
                    if not os.path.isdir(user_dir):
                        LOG.debug('User directory "' + user_dir + '" is invalid.')
                        raise UserError
                    users_on_realm_vols[user_dir] = {
                        "volume": volume_dir,
                        "realm": os.path.basename(mount_dir)
                    }
                    users_with_dirs.append(user_dir)

        intersection = all_users & users_with_dirs
        return intersection, users_on_realm_vols

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
            model_diff_count = len(list(set(old_userlist) - set(new_userlist)))

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
            os.chmod(path, int(self.new_dir_perms, 8))
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
            return set(m)

        fstab_mounts, mtab_mounts = map(tab_check, [open('/etc/fstab'), open('/etc/mtab')])
        if len(fstab_mounts & mtab_mounts) == len(fstab_mounts):
            LOG.debug('All detected PanFS mounts are mounted.')
        else:
            LOG.warn('There are panfs mounts that are NOT mounted.')
            raise UserWarning
        return mtab_mounts

# EOF
