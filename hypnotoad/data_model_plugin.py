class data_model_plugin(object):
    def setup(self):
        """Called before the plugin is asked to do anything."""
        raise NotImplementedError
 
    def teardown(self):
        """Called to allow the plugin to free anything."""
        raise NotImplementedError
 
    def user_info(self):
        """Look up user information in this data model."""
        raise NotImplementedError

    def priority_info(self):
        """Look up priority information in this data model."""
        raise NotImplementedError
