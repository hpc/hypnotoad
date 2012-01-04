#
# An ldap data model plugin for hypnotoad.
#

import ldap
import logging
import pprint

from hypnotoad import plugin

LOG = logging.getLogger('root')
PP = pprint.PrettyPrinter(indent=4)

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

            self.ldap_dn_user = "ou=" + ldap_ou_user + "," + ldap_dc
            self.ldap_dn_group = "ou=" + ldap_ou_group + "," + ldap_dc

            LOG.debug("URL: " + ldap_url)
            LOG.debug("Base DC: " + ldap_dc)
            LOG.debug("DN for groups: " + self.ldap_dn_group)
            LOG.debug("DN for users: " + self.ldap_dn_user)

            self.ldap_ctx = ldap.initialize(ldap_url)
            self.config = config
        else:
            self.plugin_enabled = False

    def teardown(self):
        """Called to allow the plugin to free anything."""

        if self.plugin_enabled:
            LOG.debug("Got to ldap plugin teardown")
            self.ldap_ctx.unbind_s()

    def get_model(self):
        """Look up information in this data model."""

        if self.plugin_enabled:
            LOG.debug("Got to ldap plugin get_model")

            users = self.ldap_ctx.search_s(self.ldap_dn_user, ldap.SCOPE_SUBTREE, '(cn=*)', ['cn', 'gidNumber', 'homeDirectory', 'uid', 'uidNumber', 'gecos', 'hpcDRMadef', 'loginShell'])
            groups = self.ldap_ctx.search_s(self.ldap_dn_group, ldap.SCOPE_SUBTREE, '(cn=*)', ['cn', 'hpcDRMshare', 'memberUid'])

            PP.pprint(users)
            PP.pprint(groups)

