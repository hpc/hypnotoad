#
# An action plugin for hypnotoad to create panasas links.
#

import datetime
import errno
import json
import logging
import os
import pprint
import shlex
import subprocess
import sys

from hypnotoad import plugin
from hypnotoad import hypnofs
from hypnotoad import notify

LOG = logging.getLogger('root')
PP = pprint.PrettyPrinter(indent=4)
FS = hypnofs.hypnofs()
NOTIFY = notify.notify()

class panlinks_plugin(plugin.action_plugin):
    def setup(self, config, model_version):
        """Called before the plugin is asked to do anything."""
        if config.getboolean('Action Options', 'panlinks_plugin_enabled'):
            self.plugin_enabled = True
            LOG.debug("Panasas Links plugin enabled")

            #
            # Gather configutation options.
            #
            self.state_dir = config.get('Basic Options', 'state_dir') + "/panlinks"
            self.new_dir_perms = config.get('Action Options', 'panlinks_new_dir_perms')

            self.root_mount_point = config.get('Action Options', 'panlinks_mount_point')

            self.skip_bad_realms = config.getboolean('Action Options', 'panlinks_skip_bad_realms')
            self.max_diff_count = config.getint('Action Options', 'panlinks_max_diff_count')
            self.max_skip_bad_vols = config.getint('Action Options', 'panlinks_max_skip_bad_vols')
            self.max_skip_bad_realms = config.getint('Action Options', 'panlinks_max_skip_bad_realms')
            self.command_timeout = config.getint('Action Options', 'panlinks_subprocess_timeout')

            # The realm skip list is comma seperated.
            self.realms_to_skip = shlex.shlex(config.get('Action Options', 'panlinks_skip_realms'))
            self.realms_to_skip.whitespace += ','
            self.realms_to_skip.whitespace_split = True

            self.create_pristine = config.getboolean('Action Options', 'panlinks_pristine_dir_create')
            self.pristine_mount_dir = config.get('Action Options', 'panlinks_pristine_mount_dir')
            self.pristine_subdir = config.get('Action Options', 'panlinks_pristine_subdir')

            self.config = config
            self.model_version = model_version

            # Initialize a place to keep track of all realm and volume failures as we go.
            self.filesystem_failures = {}
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
            self.uid_lookup_table = self.generate_uid_lookup_table(models)

            #viewmaster_users = self.collect_viewmaster_users_from_models(models)

            self.ensure_user_directories_exist(all_usernames)

            human_readable_failures = self.get_human_readable_failure_summary()
            if human_readable_failures:
                NOTIFY.email(["nfs@lanl.gov", "jonb@lanl.gov"], human_readable_failures, "Report of Panasas failures detected")

            self.log_all_filesystem_failures();

    def get_uid_for_user(self, username):
        return self.uid_lookup_table[username]

    def get_human_readable_failure_summary(self):
        output = None

        if len(self.filesystem_failures) < 1:
            return output

        output = "Hypnotoad's Panasas Failure Report!\n"
        output += "=========================================================================\n"
        output += "This is a counter of operations that took longer than '" + str(self.command_timeout) + "' seconds during a\n"
        output += "single execution of the Panasas symlinks and directory creation script.\n"
        output += "-------------------------------------------------------------------------\n"
        output += "A message of 'no_volume_specified' indicates that the list of volumes\n"
        output += "could not be determines (i.e. An 'ls' of the realm volume directory).\n"
        output += "-------------------------------------------------------------------------\n\n"

        for realm_key in self.filesystem_failures.keys():
            output += "Realm '" + str(realm_key) + "' failures:\n"
            for volume_key in self.filesystem_failures[realm_key].keys():
                output += "    * Volume '" + str(volume_key) + "' failed'" + str(self.filesystem_failures[realm_key][volume_key]) + "' time(s).\n"

            output += "\n"

        return output

    def ensure_user_directories_exist(self, all_usernames):
        """
        Check to make sure each user has a directory located on a single
        volume on each realm. Then, ensure that a symlink exists for each
        realm.
        """
        mounted_panfs_list = self.get_current_panfs_mounts()

        LOG.info("Users with accounts: " + str(len(all_usernames)))

        users_with_orig_dirs, where_user_orig_dir_is = self.get_user_original_directory_info(mounted_panfs_list, all_usernames)
        LOG.info("Users with directories: " + str(len(users_with_orig_dirs)))

        users_without_orig_dirs = []
        for u in all_usernames:
            if u not in users_with_orig_dirs:
                users_without_orig_dirs.append(u)
        LOG.info("Users with accounts, but without directories: " + str(len(users_without_orig_dirs)))

        users_with_missing_orig_dirs = {}
        for u in users_with_orig_dirs:
            if u in all_usernames:
                user_on = where_user_orig_dir_is[u]
                for realm in mounted_panfs_lit:
                    if not realm in user_on_keys():
                        if not realm in users_with_missing_orig_dirs[u]:
                            users_with_missing_orig_dirs[u].append(realm)
                    else:
                        users_with_missing_orig_dirs[u] = [realm]
        LOG.info("Users with accounts, but some missing directories: " + str(len(users_with_missing_orig_dirs.keys())))

        unknown_users_with_directories = []
        for u in users_with_orig_dirs:
            if u not in all_usernames:
                unknown_users_with_directories.append(u)
        LOG.info("Users with no account but have directories: " + str(len(unknown_users_with_directories)))
        LOG.info("List of users with no account but have directories: " + str(unknown_users_with_directories))

        if len(users_without_orig_dirs) > self.max_diff_count:
            LOG.error("Too many missing users. We have " + str(len(all_usernames)) + " total users, but only " + str(len(users_with_orig_dirs)) + " have existing directories.")
            sys.exit()

        """Create missing directories and symlinks."""
        for user in users_with_missing_orig_dirs.keys():
            for realm in users_with_missing_orig_dirs[users]:
                if not realm in self.filesystem_failures.keys():
                    self.create_missing_directories_for(user, realm)

        """Create a new set of directories and symlinks."""
        for user in users_without_orig_dirs:
            for realm in mounted_panfs_list:
                self.create_missing_directories_for(user, realm)

        """Create a pristine directory."""
        if self.create_pristine:
            pristine_users, pristine_where = self.get_user_original_directory_info(mounted_panfs_list, all_usernames)
            if FS.ismount(self.pristine_mount_dir, self.command_timeout):
                pristine_path = self.pristine_mount_dir + "/" + self.pristine_subdir
                for u in pristine_users:
                    realms = pristine_where[u].keys()
                    for r in realms:
                        if len(pristine_where[u][r]) > 1:
                            LOG.error("User '" + u + "' has a directory on more than one volume '" + v + "' in realm " + r  + "'.")
                            for v in pristine_where[u][r]:
                                LOG.info("User '" + u + "' has a directory on volume '" + v + "' in realm " + r + "'.")
                            continue
                        for v in pristine_where[u][r]:
                            self.ensure_symlink_for_user(u, os.path.basename(os.path.normpath(r)), v, pristine_path)
            else:
                LOG.error("Pristine base path was not mounted (" + str(self.pristine_mount_dir) + ").")
                sys.exit()

    def create_initial_directories_for(self, username, realm):
        """Create a new directory on each realm for the specified user."""

        realm = os.path.basename(os.path.normpath(realm))

        # More trouble in finding a volume? Then skip this realm.
        vol_name = self.get_volume_with_least_users(realm)
        if vol_name = None:
            return

        user_dir_path = self.root_mount_point + "/" + realm + "/" + vol_name + "/" + username

        # Skip realms that may be having trouble  
        if realm in self.filesystem_failures.keys():  
            #LOG.warning("Due to failure, not creating new user directory on '" + realm + "'.")  
            return  

        LOG.debug('Creating initial user directory "' + user_dir_path + '" for user "' + username)
        self.ensure_dir(user_dir_path)

        LOG.debug('Chowning new directory to "' + username + '":users.')
        kwargs = { 'path': user_dir_path, 'owner': self.get_uid_for_user(username), 'group': "users", 'timeout': self.command_timeout }
        self.catch_blocking_filesystem_exception(realm, vol_name, FS.chown, **kwargs)

        LOG.info('Creating new symlink for user "' + username + '" on realm "' + realm + '".')
        self.ensure_symlink_for_user(username, realm, vol_name, "/")

    def ensure_symlink_for_user(self, username, realm_name, volume_name, base):
        """
        Ensure that a symlink exists for the user in the specified location.
        """

        user_symlink_dst_path = base + "/" + realm_name + "/" + username
        user_symlink_src_path = self.root_mount_point + "/" + realm_name + "/" + volume_name + "/" + username

        kwargs = { 'path': user_symlink_dst_path, 'timeout': self.command_timeout }  
        if not self.catch_blocking_filesystem_exception(realm_name, volume_name, FS.path_exists, **kwargs): 
            LOG.debug('Creating missing symlink from "' + user_symlink_src_path + '" to "' + user_symlink_dst_path)

            kwargs = { 'src': user_symlink_src_path, 'dest': user_symlink_dst_path, 'timeout': self.command_timeout }
            self.catch_blocking_filesystem_exception(realm_name, volume_name, FS.symlink, **kwargs)

            kwargs = { 'path': user_symlink_dst_path, 'timeout': self.command_timeout }
            if not self.catch_blocking_filesystem_exception(realm_name, volume_name, FS.islink, **kwargs):
                LOG.error('Failed to create a symlink at: "' + user_symlink_dst_path + '".')

    def generate_uid_lookup_table(self, models):
        """Generate a table to lookup uids from usernames."""
        uid_lookup = {}
        for plug_model in models:
            for m in plug_model:
                if 'user_entry' in m.keys():
                    user = m['user_entry']
                    uid = user['user_id_integer']

                    uid_lookup[user['short_name_string']] = uid
        return uid_lookup

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

        realm = self.root_mount_point + "/" + realm

        kwargs = { 'path': realm, 'timeout': self.command_timeout }
        if not self.catch_blocking_filesystem_exception(realm, None, FS.isdir, **kwargs):
            LOG.warning('The specified realm path "' + realm + '" does not exist.')
            return None

        kwargs = { 'path': realm, 'timeout': self.command_timeout }
        for volume_dir in self.catch_blocking_filesystem_exception(realm, None, FS.listdir, **kwargs):
            if not FS.isdir(volume_dir, self.command_timeout):
                LOG.warning('Found a volume that is not a directory (' + volume_dir + ').')
                continue

            if not volume_dir.startswith("vol"):
                continue

            volume_path = realm + "/" + volume_dir
            LOG.debug("Checking volume " + volume_path + " on realm " + realm)

            kwargs = { 'path': volume_path, 'timeout': self.command_timeout }
            users_in_this_volume = len(self.catch_blocking_filesystem_exception(realm, volume_dir, FS.listdir, **kwargs))
            if current_least_count is None or users_in_this_volume < current_least_count:
                volume_with_least_users = volume_dir
                current_top_count = users_in_this_volume

        if volume_with_least_users is None:
            LOG.warning("Could not find a volume with the least number of users: " + volume_with_least_users)
            return None

        LOG.debug("Found the volume with the least number of users: " + volume_with_least_users)
        return volume_with_least_users

    def get_user_original_directory_info(self, mounts, all_users):
        """
        Find valid users which already have directories created, as well as
        what volume users have directories on.
        """
        where_users_on_realm_vols = {}
        users_with_dirs = []

        for mount_dir in mounts:

            kwargs = { 'path': mount_dir, 'timeout': self.command_timeout }
            for volume_dir in self.catch_blocking_filesystem_exception(mount_dir, None, FS.listdir, **kwargs):
                if not volume_dir.startswith("vol"):
                    continue

                volume_path = mount_dir + "/" + volume_dir
                volume_path = volume_path.strip()
#                LOG.debug("Found volume at: + volume_path)

                kwargs = { 'path': volume_path, 'timeout': self.command_timeout }
                if not self.catch_blocking_filesystem_exception(mount_dir, volume_dir, FS.isdir, **kwargs):
                    LOG.warning('Volume directory "' + volume_path + '" is invalid.')
                    continue

                kwargs = { 'path': volume_path, 'timeout': self.command_timeout }
                for user_dir in self.catch_blocking_filesystem_exception(mount_dir, volume_dir, FS.listdir, **kwargs):
                    user_path = volume_path + "/" + user_dir
                    user_path = user_path.strip()

                    """Ignore lost and found dirs."""
                    if user_dir.strip().startswith("Lost+Found"):
                        continue

                    """I have no idea why there are key files in there."""
                    if user_dir.strip().startswith("id_rsa.pub"):
                        continue

                    """Ignore the obvious PLFS files."""
                    if user_dir.strip().startswith(".plfs"):
                        continue

                    """On a rare occation, we'll see gzips in there."""
                    if user_dir.strip().endswith(".tgz"):
                        continue

                    """Dunno why there would be tar files in there, but it's happened."""
                    if user_dir.strip().endswith(".tar"):
                        continue

                    """Lets ignore gz for good luck. Who knows."""
                    if user_dir.strip().endswith(".gz"):
                        continue

#                    LOG.debug("Found user at: " + user_path)

                    kwargs = { 'path': user_path, 'timeout': self.command_timeout }
                    if not self.catch_blocking_filesystem_exception(mount_dir, volume_dir, FS.isdir, **kwargs):
                        LOG.warning('User directory "' + user_path + '" is invalid.')
                        continue

                    if not user_dir in where_users_on_realm_vols:
                        where_users_on_realm_vols[user_dir] = {
                            mount_dir: [
                                volume_dir,
                            ]
                        }
                    else:
                        if not mount_dir in where_users_on_realm_vols[user_dir]:
                            where_users_on_realm_vols[user_dir][mount_dir] = [
                                volume_dir,
                            ]
                        else:
                            where_users_on_realm_vols[user_dir][mount_dir].append(volume_dir)


                    if not user_dir.strip() == volume_dir.strip():
                        if not user_dir.strip() in users_with_dirs:
                            users_with_dirs.append(user_dir.strip())

        return users_with_dirs, where_users_on_realm_vols

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
            LOG.debug("Saving to json at: " + dest_file_name)
            j = json.dumps(obj)
            f = open(dest_file_name, 'w')
            f.write(j + "\n")
            f.close()

        def json_to_models(json_file_name):
            LOG.debug("Reading in json file at: " + json_file_name)
            f = open(json_file_name)
            return json.load(f)

        if FS.isfile(cache_file_name):
            old_models = json_to_models(cache_file_name)

            old_userlist, new_userlist = map(self.collect_users_from_models, [old_models, models])
            model_diff_count = len(list(set(old_userlist) - set(new_userlist)))

            if model_diff_count > self.max_diff_count:
                LOG.error("Model too different with " + model_diff_count + " changes.")
                raise UserWarning
            else:
                # Overwrite the old cache.
                LOG.debug("Verified existing model as sane. We can safely continue.")
                save_as_json(models, cache_file_name)
        else:
            # Create a new cache if one does not exist.
            save_as_json(models, cache_file_name)

    def ensure_dir(self, path):
        """Create directory at path if it doesn't exist."""
        LOG.debug("Ensure dir at '" + path + "' with perms '" + self.new_dir_perms + "'.")
        try:
            kwargs = { 'path': path, 'timeout': self.command_timeout }
            self.catch_blocking_filesystem_exception(path, None, FS.makedirs, **kwargs)

            kwargs = { 'path': path, 'perms': self.new_dir_perms, 'timeout': self.command_timeout }
            self.catch_blocking_filesystem_exception(path, None, FS.chmod, **kwargs)
        except OSError, exc:
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
            LOG.info('All detected PanFS mounts are mounted.')
        else:
            LOG.warning('There are panfs mounts that are NOT mounted.')

        skips = list(self.realms_to_skip)
        for s in skips:
            LOG.debug("Configuration requires skipping realm: '" + str(s) + "'.")
            mtab_mounts.discard(s)

        LOG.info("Using realms: " + str(mtab_mounts))
        return mtab_mounts

    def catch_blocking_filesystem_exception(self, realm_name, volume_name, func, **kwargs):
        """
        Check for blocking filesystem operations and increment the relevant
        failure counter. Then, verify that failure counters do not exceed
        configuration limits.
        """
        if volume_name is None:
            volume_name = "<no_volume_specified>"
            LOG.debug("Checking blocking exc on realm = '" + realm_name + "' volume = '" + volume_name + "'.")

        is_throwing, result = FS.throws_blocking_filesystem_exception(func, **kwargs)
        if is_throwing:
            LOG.debug("Encountered a timeout on volume '" + realm_name + "/" + volume_name + "'. Attempting to continue.")

            if not self.filesystem_failures.has_key(realm_name):
                self.filesystem_failures[realm_name] = {}

            if not self.filesystem_failures[realm_name].has_key(volume_name):
                self.filesystem_failures[realm_name][volume_name] = 1
            else:
                self.filesystem_failures[realm_name][volume_name] = self.filesystem_failures[realm_name][volume_name] + 1

            self.check_blocking_failure_counters()

        if result is None:
            result = []

        return result

    def log_all_filesystem_failures(self):
        if len(self.filesystem_failures) > 0:
            LOG.info("Summary of failures detected during this run: " + str(self.filesystem_failures))

            for realm_key in self.filesystem_failures.keys():
                for volume_key in self.filesystem_failures[realm_key].keys():
                    # This info messsage is tailored for parsing by splunk
                    LOG.info("Hypnotoad filesystem failure detected: realm=" + str(os.path.basename(os.path.normpath(realm_key))) + " volume=" + str(volume_key) + \
                             " count=" + str(self.filesystem_failures[realm_key][volume_key]) + " timeout=" + str(self.command_timeout))
        else:
            LOG.info("No failures detected during this run.")

    def check_blocking_failure_counters(self):
        """Check to see if failures exceed configuration."""
        total_realm_failures = 0

        LOG.debug("Failures = " + str(self.filesystem_failures))

        for realm_key in self.filesystem_failures.iterkeys():
            total_vol_failures = 0

            for volume_key in self.filessytem_failures[realm_key].iterkeys():
                total_vol_failures += 1

            if total_vol_failures > self.max_skip_bad_vols:
                #LOG.warning("Realm '" + realm_key + "' has failed with at least " + str(self.max_skip_bad_vols) + " volume failures.")
                total_realm_failures += 1

        if total_realm_failures > self.max_skip_bad_realms:
            LOG.critical("Realm failures '" + str(total_realm_failures) + "' exceeds '" + str(self.max_skip_bad_realms) + "' configuration limit. This is really bad, so we're going to exit the program now.")

            self.log_all_filesystem_failures()
            sys.exit()

        return

# EOF
