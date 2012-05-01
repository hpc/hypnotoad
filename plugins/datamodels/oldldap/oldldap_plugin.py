#
# An ldap data model plugin for hypnotoad. This is for legacy use of LANL's
# old LDAP schema.
#

import ldap
import logging
import json

from hypnotoad import plugin

LOG = logging.getLogger('root')

class oldldap_plugin(plugin.data_model_plugin):
    def setup(self, config, model_version):
        """Called before the plugin is asked to do anything."""

        if config.getboolean('Data Model Options', 'oldldap_plugin_enabled'):
            self.plugin_enabled = True
            LOG.debug("OLD LDAP plugin enabled")

            ldap_url = config.get('Data Model Options', 'oldldap_server')
            self.ldap_dc  = config.get('Data Model Options', 'oldldap_dc')

            ldap_timeout = config.getfloat( \
                'Data Model Options', 'oldldap_timeout')

            self.use_groups = config.getboolean( \
                'Data Model Options', 'oldldap_use_groups')

            # Check to see what OUs map to what compartment.
            self.user_compartment_ous = json.loads(config.get( \
                'Data Model Options', 'oldldap_user_compartment_ous'))

            for compartment, ous in self.user_compartment_ous.iteritems():
                LOG.debug("Populating compartment `" + compartment + \
                    "' with OUs  `" + str(set(ous)) + "'.")

            LOG.debug("URL: " + ldap_url)
            LOG.debug("Base DC: " + self.ldap_dc)

            self.ldap_ctx = ldap.initialize(ldap_url)
            self.ldap_ctx.set_option(ldap.OPT_NETWORK_TIMEOUT, ldap_timeout)

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

            for compartment, ou_names in self.user_compartment_ous.iteritems():

                for ou_name in ou_names:

                    ldap_user_dn = "ou=" + ou_name + "," + self.ldap_dc
                    LOG.debug("Looking up DN: `" + ldap_user_dn + "'.")

                    users = ldap_search(ldap_user_dn, [
                        'cn', 'gidNumber', 'homeDirectory', 'uid',
                        'uidNumber', 'gecos', 'loginShell'
                    ])

                    if self.use_groups:
                        # TODO:
                        # Go though each group and remove users that are not
                        # included in a group.
                        raise NotImplementedError

                    LOG.debug("Populating model for compartment `" + \
                        compartment + "' with OU `" + str(ou_name) + \
                        "' (`" + str(len(users)) + "' users).")

                    for u in users:
                        dn, attrs = u

                        model.append({'user_entry': {
                            'short_name_string': attrs['uid'][0],
                            'full_name_string': attrs['cn'][0],
                            'group_id_integer': attrs['gidNumber'][0],
                            'user_id_integer': attrs['uidNumber'][0],
                            'home_directory_string': attrs['homeDirectory'][0],
                            'login_shell_string': attrs['loginShell'][0],
                            'compartment_access_array': [compartment]
                    }})

        return model

# EOF
