#
# Base classes for use in the Panasas symlinks action.
#


class ScratchUser(object):

    def __init__(self, short_name, uid="-1", gid="-1"):
        self.short_name = short_name
        self.uid = uid
        self.gid = gid
        self.compartments = []
        self.volumes = []
        self.homes = []


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


class ScratchHome(object):

    def __init__(self, realm, volume, compartment, user):
        self.realm = realm
        self.volume = volume
        self.compartment = compartment
        self.user = user
        self.absolute_path = None

    def __key(self):
        return (self.absolute_path, self.compartment)

    def __eq__(x, y):
        return x.__key() == y.__key()

    def __hash__(self):
        return hash(self.__key())

    def __repr__(self):
        result = "ScratchHome: `" + self.absolute_path + \
            "' in compartment `" + \
            self.compartment.short_name + "'."
        return result


class ScratchCompartment(object):

    def __init__(self, short_name, regex=None):
        self.regex = regex
        self.short_name = short_name
        self.volumes = []

    def __key(self):
        """
        FIXME: possible bug here since we don't hash the volumes.
        """
        return (self.regex, self.short_name)

    def __eq__(x, y):
        return x.__key() == y.__key()

    def __hash__(self):
        return hash(self.__key())

    def __repr__(self):
        result = "ScratchCompartment: `" + self.short_name + "'."
        return result

# EOF
