#
# Abstract base classes for plugin types.
#

class data_model_plugin(object):
    def setup(self, config):
        """Called before the plugin is asked to do anything."""
        raise NotImplementedError
 
    def teardown(self):
        """Called to allow the plugin to free anything."""
        raise NotImplementedError
 
    def get_model(self):
        """Look up information in this data model."""
        raise NotImplementedError

class action_plugin(object):
    def setup(self, config):
        """Called before the plugin is asked to do anything."""
        raise NotImplementedError
 
    def teardown(self):
        """Called to allow the plugin to free anything."""
        raise NotImplementedError

    def append_model(self, model):
        """Return the model information formatted for this action."""
        raise NotImplementedError
