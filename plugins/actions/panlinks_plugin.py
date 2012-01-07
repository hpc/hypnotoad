#
# A action plugin for hypnotoad to create panasas links.
#

from hypnotoad import plugin
import logging
import pprint

LOG = logging.getLogger('root')
PP = pprint.PrettyPrinter(indent=4)

class panlinks_plugin(plugin.action_plugin):
    def setup(self, config, model_version):
        """Called before the plugin is asked to do anything."""

        if config.getboolean('Action Options', 'panlinks_plugin_enabled'):
            self.plugin_enabled = True
            LOG.debug("Panasas Links plugin enabled")

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

#            for plug_model in models:
#                for m in plug_model:
#                    if 'user_entry' in m.keys():

# EOF
