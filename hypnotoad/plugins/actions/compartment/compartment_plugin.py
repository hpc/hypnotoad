#
# A plugin to generate a user to compartment mapping.
#

import datetime
import logging
import pprint

from hypnotoad.core import plugin

LOG = logging.getLogger('root')
PP = pprint.PrettyPrinter(indent=4)

class compartment_plugin(plugin.action_plugin):
    def setup(self, config, model_version):
        """Called before the plugin is asked to do anything."""

        if config.getboolean('Action Options', 'compartment_plugin_enabled'):
            self.plugin_enabled = True
            LOG.debug("compartment mapping generator plugin enabled")

            # Get the location to write the map to.
            self.map_output_file = config.get('Action Options', 'compartment_output_location')

            self.config = config
            self.model_version = model_version
        else:
            self.plugin_enabled = False

    def teardown(self):
        """Called to allow the plugin to free anything."""

        if self.plugin_enabled:
            LOG.debug("Got to compartment mapping plugin teardown")

    def append_model(self, models):
        """Handled a model appended to this output."""

        if self.plugin_enabled:
            LOG.debug("Got to compartment mapping generator plugin append_model.")

            users = {}

            for plug_model in models:
                for m in plug_model:
                    if 'user_entry' in m.keys():
                        user = m['user_entry']

                        short_name = user['short_name_string'].strip()
                        users[short_name] = list(set(user['compartment_access_array'] + \
                            users.setdefault(short_name, [])))

            LOG.debug("Writing compartment map to `" + self.map_output_file + "'.")

            outfile = open(self.map_output_file,"w")

            outfile.write('#\n# This file is intended for non-security sensitive compartment\n')
            outfile.write('# operations, such as module environment loading.\n#\n')

            outfile.write('# Generated on: ' + \
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M") + '\n#\n\n')

            for k in users:
                outfile.write('%s:%s\n' % (k, ",".join(users[k])))

            outfile.write('\n# EOF\n')
            outfile.close()

# EOF
