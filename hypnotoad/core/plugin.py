#
# Abstract base classes for plugin types.
#


class data_model_plugin(object):

    def setup(self, config):
        """Called before the plugin is asked to do anything."""
        raise NotImplementedError

    def teardown(self):
        """Called to allow the plugin a clean shutdown."""
        raise NotImplementedError

    def get_model(self):
        """Look up information in this data model."""
        raise NotImplementedError


class action_plugin(object):

    def setup(self, config):
        """Called before the plugin is asked to do anything."""
        raise NotImplementedError

    def teardown(self):
        """Called to allow the plugin a clean shutdown."""
        raise NotImplementedError

    def append_model(self, model):
        """Handle the model information for this action."""
        raise NotImplementedError
