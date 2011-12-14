class scheduler_plugin(object):
    def setup(self):
        """Called before the plugin is asked to do anything."""
        raise NotImplementedError
 
    def teardown(self):
        """Called to allow the plugin to free anything."""
        raise NotImplementedError

    def user_output(self):
        """Return user information formatted for this scheduler."""
        raise NotImplementedError

    def priority_output(self):
        """Return priority information formatted for this scheduler."""
        raise NotImplementedError
