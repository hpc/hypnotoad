#
# A moab idcfg action plugin for hypnotoad.
#

import logging
import os
import sys

sys.path.append(os.path.abspath('plugins/actions/moab'))

from hypnotoad import plugin
from moab_credential import *

LOG = logging.getLogger('root')

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

        moab_credentials = []

        if self.plugin_enabled:
            LOG.debug("Got to moab plugin append_model.")

            for plug_model in models:
                for m in plug_model:
                    if 'group_entry' in m.keys():
                        group = m['group_entry']

                        group_cred = MoabCredential("group", group['short_name_string'])
                        group_cred.add_attribute("fstarget", group['priority_fairshare_float'])

                        moab_credentials.append(group_cred)

        for cred in moab_credentials:
            LOG.debug("Moab credential idcfg: `" + str(cred) + "'.")

# EOF
