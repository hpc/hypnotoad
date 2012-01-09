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

            self.cache_check_and_update(models)

#            for plug_model in models:
#                for m in plug_model:
#                    if 'user_entry' in m.keys():

    def cache_check_and_update(self, models):
        """
        If a cache exists, check differences and update the cache if the
        differences are not too great. Otherwise quietly create a cache if one
        does not exist already.
        """
        cache_file_name = self.state_dir + "/" + "model.json"
        self.ensure_dir(self.state_dir)

        if os.path.isfile(cache_file_name):
            old_model = self.json_to_models(cache_file_name)
            model_diff_count = count_model_diff(old_model, models)

            if model_diff_count > self.max_diff_count:
                LOG.error("Model too different with " + model_diff_count + " changes.")
                raise UserWarning
            else:
                # Overwrite the old cache.
                self.save_as_json(models, cache_file_name)
        else:
            # Create a new cache if one does not exist.
            self.save_as_json(models, cache_file_name)

    def save_as_json(self, obj, dest_file_name):
        """Serializes obj to json and saves to a file at dest."""
        j = json.dumps(obj)
        f = open(dest_file_name, 'w')
        f.write(j + "\n")
        f.close()

    def json_to_models(self, json_file_name):
        raise NotImplementedError

    def ensure_dir(self, path):
        """Create directory at path if it doesn't exist."""
        try:
            os.makedirs(path)
        except OSError as exc:
            if exc.errno == errno.EEXIST:
                pass
            else: raise

# EOF
