#
# Helpers related to handling failures.
#

class FailureHelper:

    def __init__(self, config):
        self.max_skip_bad_realms = config.getint('Action Options', 'nfsdirs_max_skip_bad_realms')
        self.command_timeout = config.getint('Action Options', 'nfsdirs_subprocess_timeout')

    def get_human_readable_failure_summary(self):
        """
        This function outputs text suitable for emailing to administrators.
        """
        output = None

        if len(self.filesystem_failures) < 1:
            return output

        output = "Hypnotoad's Filer Dirs Failure Report!\n"
        output += "=========================================================================\n"
        output += "This is a counter of operations that took longer than '" + \
            str(self.command_timeout) + "' seconds during a\n"
        output += "single execution of the nfs user directory creation script.\n"
        output += "-------------------------------------------------------------------------\n\n"

        for realm_key in self.filesystem_failures.keys():
            output += "Realm '" + str(realm_key) + "' failures:\n"

        return output

    def check(self, realms):
       """
       This will check the configuration thresholds on failures for each realm
       as well as update realm failure counters.
       """
       total_failed_realms = 0

       if total_failed_realms > self.max_skip_bad_realms:
           LOG.critical("Realm failures '" + str(total_realm_failures) + \
               "' exceeds '" + str(self.max_skip_bad_realms) + \
               "' configuration limit. This is really bad, so we're going" + \
               " to exit the program now.")
           sys.exit()

       return

# EOF
