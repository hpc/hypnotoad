#
# Base classes for use in the Panasas symlinks action.
#

class ScratchUser(object):
    def __init__(self, short_name):
        self.short_name = short_name
        self.compartments = []
        self.volumes = []
        self.homes = []

class ScratchHome(object):
    def __init__(self, realm, volume, compartment, user):
        self.realm = realm
        self.volume = volume
        self.compartment = compartment
        self.user = user
        self.absolute_path = None

class ScratchRealm(object):
    def __init__(self, base_name):
        self.compartments = []
        self.failures = []
        self.base_name = base_name
        self.absolute_path = None
        self.containing_path = None
        self.has_failed = False

class ScratchVolume(object):
    def __init__(self, base_name, realm, compartment):
        self.base_name = base_name
        self.realm = realm
        self.users = []
        self.absolute_path = None
        self.has_failed = False
        self.compartment = compartment

class ScratchFailure(object):
    def __init__(self, message, volume=None):
        self.message = message
        self.volume = volume

class ScratchCompartment(object):
    def __init__(self, short_name, regex=None):
        self.regex = regex
        self.short_name = short_name
        self.volumes = []

# EOF
