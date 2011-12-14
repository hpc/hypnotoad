#
# A moab scheduler plugin for hypnotoad.
#

from hypnotoad import plugin
import ldap
import logging

LOG = logging.getLogger('root')

class moab(plugin.scheduler_plugin):
    def setup(self):
        """Called before the plugin is asked to do anything."""
        LOG.debug("Got to moab setup")

    def teardown(self):
        """Called to allow the plugin to free anything."""
        LOG.debug("Got to moab teardown")

    def user_output(self, outputs):
        """Return user information formatted for moab."""
        LOG.debug("Got to moab user_output")

    def priority_output(self, outputs):
        """Return priority information formatted for moab."""
        LOG.debug("Got to moab priority_output")
