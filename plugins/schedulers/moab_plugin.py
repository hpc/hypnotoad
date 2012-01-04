#
# A moab scheduler plugin for hypnotoad.
#

from hypnotoad import plugin
import ldap
import logging
import pprint

LOG = logging.getLogger('root')
PP = pprint.PrettyPrinter(indent=4)

class moab_plugin(plugin.scheduler_plugin):
    def setup(self, config, model_version):
        """Called before the plugin is asked to do anything."""

        if config.getboolean('Scheduler Options', 'moab_plugin_enabled'):
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

                        name = group['short_name_string']
                        fstarget = group['priority_fairshare_float']

                        LOG.debug('Config entry: GROUPCFG[%s] FSTARGET=%s' % (name, fstarget))

#            PP.pprint(model)
