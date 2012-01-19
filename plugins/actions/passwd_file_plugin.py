#
# A passwd file generator action plugin for hypnotoad.
#

from hypnotoad import plugin
import logging
import pprint

LOG = logging.getLogger('root')
PP = pprint.PrettyPrinter(indent=4)

class passwd_file_plugin(plugin.action_plugin):
    def setup(self, config, model_version):
        """Called before the plugin is asked to do anything."""

        if config.getboolean('Action Options', 'passwd_file_plugin_enabled'):
            self.plugin_enabled = True
            LOG.debug("passwd file generator plugin enabled")

            self.config = config
            self.model_version = model_version
        else:
            self.plugin_enabled = False

    def teardown(self):
        """Called to allow the plugin to free anything."""

        if self.plugin_enabled:
            LOG.debug("Got to passwd file generator plugin teardown")

    def append_model(self, models):
        """Handled a model appended to this output."""

        if self.plugin_enabled:
            LOG.debug("Got to passwd file generator plugin append_model.")

            for plug_model in models:
                for m in plug_model:
                    if 'user_entry' in m.keys():
                        user = m['user_entry']

                        short_name = user['short_name_string'].strip()
                        full_name = user['full_name_string'].strip()
                        gid = user['group_id_integer']
                        uid = user['user_id_integer']
                        homedir = user['home_director_string']
                        shell = user['login_shell_string']

                        print '%s:x:%s:%s:%s:%s:%s' % (short_name, uid, gid, full_name, homedir, shell)

# EOF
