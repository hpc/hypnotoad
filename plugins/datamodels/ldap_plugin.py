#
# An ldap data model plugin for hypnotoad.
#

from hypnotoad import plugin
import ldap
import logging

LOG = logging.getLogger('root')

class ldap_plugin(plugin.data_model_plugin):
    ldap_dc  = None
    ldap_url = None
    ldap_ou  = None

    def setup(self, config):
        """Called before the plugin is asked to do anything."""

        if config.getboolean('Data Model Options', 'ldap_plugin_enabled'):
            self.plugin_enabled = True
            LOG.debug("LDAP plugin enabled")

            ldap_url = config.get('Data Model Options', 'ldap_server')
            ldap_dc  = config.get('Data Model Options', 'ldap_dc')

            ldap_ou_group = config.get('Data Model Options', 'ldap_ou_group')
            ldap_ou_user = config.get('Data Model Options', 'ldap_ou_user')

            LOG.debug("URL: " + ldap_url)
            LOG.debug("Base DC:  " + ldap_dc)
            LOG.debug("DN for groups:  DC=" + ldap_ou_group + "," + ldap_dc)
            LOG.debug("DN for users:  DC=" + ldap_ou_user + "," + ldap_dc)
#            self.ldap_ctx = ldap.initialize(ldap_url)

            self.config = config
        else:
            self.plugin_enabled = False

    def teardown(self):
        """Called to allow the plugin to free anything."""

        if self.plugin_enabled:
            LOG.debug("Got to ldap plugin teardown")
#            self.ldap_ctx.unbind_s()

    def get_model(self):
        """Look up information in this data model."""

        if self.plugin_enabled:
            LOG.debug("Got to ldap plugin get_model")
