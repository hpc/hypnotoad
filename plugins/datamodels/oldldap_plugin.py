#
# An ldap data model plugin for hypnotoad. This is for legacy use of LANL's
# old LDAP schema.
#

import ldap
import logging

from hypnotoad import plugin

LOG = logging.getLogger('root')

class oldldap_plugin(plugin.data_model_plugin):
    def setup(self, config, model_version):
        """Called before the plugin is asked to do anything."""

        if config.getboolean('Data Model Options', 'oldldap_plugin_enabled'):
            self.plugin_enabled = True
            LOG.debug("OLD LDAP plugin enabled")

            ldap_url = config.get('Data Model Options', 'oldldap_server')
            ldap_dc  = config.get('Data Model Options', 'oldldap_dc')
            ldap_user_ou = config.get('Data Model Options', 'oldldap_user_ou')

            self.use_groups = config.getboolean('Data Model Options', 'oldldap_use_groups')
            self.ldap_user_dn = "ou=" + ldap_user_ou + "," + ldap_dc

            LOG.debug("URL: " + ldap_url)
            LOG.debug("Base DC: " + ldap_dc)
            LOG.debug("Users DN: " + self.ldap_user_dn)

            self.ldap_ctx = ldap.initialize(ldap_url)

            self.config = config
            self.model_version = model_version
        else:
            self.plugin_enabled = False

    def teardown(self):
        """Called to allow the plugin to free anything."""

        if self.plugin_enabled:
            LOG.debug("Got to OLD ldap plugin teardown")
            self.ldap_ctx.unbind_s()

    def get_model(self):
        """Look up information in this data model."""

        model = []

        if self.plugin_enabled:
            LOG.debug("Got to OLD ldap plugin get_model")

            model.append({'little_lang_entry':{'version':self.model_version}}) 

            def ldap_search(dn, attrs):
                return self.ldap_ctx.search_s(dn, ldap.SCOPE_SUBTREE, '(cn=*)', attrs)

            users = ldap_search(self.ldap_user_dn, [
                'cn', 'gidNumber', 'homeDirectory', 'uid',
                'uidNumber', 'gecos', 'loginShell'
            ])

            if self.use_groups:
                #
                # TODO:
                # Go though each group and remove users that are not included in a group.
                #
                raise NotImplementedError

            for u in users:
                dn, attrs = u
                LOG.debug("Found user with DN: " + dn) 
                model.append({'user_entry': {
                    'short_name_string': attrs['uid'][0],
                    'full_name_string': attrs['cn'][0],
                    'group_id_integer': attrs['gidNumber'][0],
                    'user_id_integer': attrs['uidNumber'][0],
                    'home_directory_string': attrs['homeDirectory'][0],
                    'login_shell_string': attrs['loginShell'][0],
                }})

        return model

# EOF
