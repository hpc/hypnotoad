#
# An ldap data model plugin for hypnotoad.
#

import ldap
import logging

from hypnotoad import plugin

LOG = logging.getLogger('root')

class ldap_plugin(plugin.data_model_plugin):
    ldap_dc  = None
    ldap_url = None
    ldap_ou  = None

    def setup(self, config, model_version):
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
            self.model_version = model_version
        else:
            self.plugin_enabled = False

    def teardown(self):
        """Called to allow the plugin to free anything."""

        if self.plugin_enabled:
            LOG.debug("Got to ldap plugin teardown")
            self.ldap_ctx.unbind_s()

    def get_model(self):
        """Look up information in this data model."""

        model = []

        if self.plugin_enabled:
            LOG.debug("Got to ldap plugin get_model")

            model.append({'little_lang_entry':{'version':self.model_version}}) 

            def ldap_search(dn, attrs):
                return self.ldap_ctx.search_s(dn, ldap.SCOPE_SUBTREE, '(cn=*)', attrs)

            users = ldap_search(self.ldap_dn_user, [
                'cn', 'gidNumber', 'homeDirectory', 'uid',
                'uidNumber', 'gecos', 'hpcDRMadef', 'loginShell'
            ])

            for u in users:
                dn, attrs = u
                LOG.debug("Found user with DN: " + dn) 
                model.append({'user_entry': {
                    'short_name_string': attrs['uid'],
                    'full_name_string': attrs['cn'],
                    'group_id_integer': attrs['gidNumber'],
                    'user_id_integer': attrs['uidNumber'],
                    'home_directory_string': attrs['homeDirectory'],
                    'login_shell_string': attrs['loginShell'],
                    'priority_fairshare_float': '',
                    'priority_qos_name_array': ''
                }})

            groups = ldap_search(self.ldap_dn_group, ['cn', 'hpcDRMshare', 'memberUid'])

            for g in groups:
                dn, attrs = g
                LOG.debug("Found group with DN: " + dn)
                model.append({'group_entry': {
                    'short_name_string': attrs['cn'],
                    'priority_fairshare_float': attrs['hpcDRMshare'],
                }})

        return model

# EOF
