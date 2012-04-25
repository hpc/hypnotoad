#
# A moab action plugin for hypnotoad.
#

from hypnotoad import plugin
import logging
import pprint

LOG = logging.getLogger('root')
PP = pprint.PrettyPrinter(indent=4)

class moab_plugin(plugin.action_plugin):
    def setup(self, config, model_version):
        """Called before the plugin is asked to do anything."""

        if config.getboolean('Action Options', 'moab_plugin_enabled'):
            self.plugin_enabled = True
            LOG.debug("moab plugin enabled")

            self.config = config
            self.model_version = model_version
        else:
            self.plugin_enabled = False

    def teardown(self):
        """Called to allow the plugin to free anything."""

        if self.plugin_enabled:
            LOG.debug("Got to moab plugin teardown")

    def append_model(self, models):
        """Handled a model appended to this output."""

        if self.plugin_enabled:
            LOG.debug("Got to moab plugin append_model.")

            for plug_model in models:
                for m in plug_model:
                    if 'group_entry' in m.keys():
                        group = m['group_entry']

                        name = group['short_name_string'].strip()
                        fstarget = group['priority_fairshare_float'].strip()

                        if fstarget:
                            print 'GROUPCFG[%s] FSTARGET=%s' % (name, fstarget)
                        else:
                            LOG.debug('Group "' + name + '" did not have a fairshare value.')
                    if 'user_entry' in m.keys():
                        user = m['user_entry']

                        name = user['short_name_string'].strip()
                        LOG.debug("Found user in model with name: " + name)

# EOF
