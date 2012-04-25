class ScratchUser:
    def __init__(self, short_name):
        self.short_name = short_name
        self.volumes = []

class ScratchHome:
    def __init__(self, realm, volume, compartment, user):
        self.realm = realm
        self.volume = volume
        self.compartment = compartment
        self.user = user

class ScratchRealm:
    def __init__(self, base_name):
        self.compartments = []
        self.failures = []
        self.base_name = base_name

class ScratchVolume:
    def __init__(self, base_name, realm):
        self.realm = realm
        self.users = []
        self.failures = []    

class ScratchFailure:
    def __init__(self, message, realm, volume):
        self.message = message
        self.realm = realm
        self.volume = volume

class ScratchCompartment:
    def __init__(self, regex, short_name):
        self.regex = regex
        self.short_name = short_name

# EOF
