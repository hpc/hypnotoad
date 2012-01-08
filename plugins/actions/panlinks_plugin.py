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

    def cache_check(self, models):
        """If a cache exists, check differences. Otherwise, create a cache."""
        cache_file_name = self.state_dir + "/" + "model.json"
        self.ensure_dir(self.state_dir)

        if os.path.isfile(cache_file_name):
            # TODO compare old cache and current model
            raise NotImplementedError
        else:
            self.save_as_json(models, cache_file_name)

    def save_as_json(self, obj, dest):
        """Serializes obj to json and saves to a file at dest."""
        j = json.dumps(obj)
        f = open(dest, 'w')
        f.write(j + "\n")
        f.close()

    def ensure_dir(self, path):
        """Create directory at path if it doesn't exist."""
        try:
            os.makedirs(path)
        except OSError as exc:
            if exc.errno == errno.EEXIST:
                pass
            else: raise

    def append_model(self, models):
        """Handled a model appended to this output."""
        if self.plugin_enabled:
            LOG.debug("Got to Panasas Links plugin append_model.")

            self.cache_check(models)

#            for plug_model in models:
#                for m in plug_model:
#                    if 'user_entry' in m.keys():

# EOF
