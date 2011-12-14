#
# A moab scheduler plugin for hypnotoad.
#

from hypnotoad import hypnolog, plugin
import ldap

LOG = hypnolog.setup_logger('root')

class moab(plugin.scheduler_plugin):
    def setup(self):
        """Called before the plugin is asked to do anything."""
        LOG.debug("Got to moab setup")

    def teardown(self):
        """Called to allow the plugin to free anything."""
        LOG.debug("Got to moab teardown")

    def user_output(self):
        """Return user information formatted for moab."""
        LOG.debug("Got to moab user_output")
        raise NotImplementedError

    def priority_output(self):
        """Return priority information formatted for moab."""
        LOG.debug("Got to moab priority_output")
