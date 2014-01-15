#
# Base classes for use in the nfsdirs plugin.
#


class ScratchUser(object):

    def __init__(self, short_name, uid="-1", gid="-1"):
        self.short_name = short_name
        self.uid = uid
        self.gid = gid
        self.compartments = []
        self.homes = []


class ScratchRealm(object):

    def __init__(self, base_name):
        self.compartments = []
        self.failures = []
        self.base_name = base_name
        self.absolute_path = None
        self.containing_path = None
        self.has_failed = False
        self.users = []


class ScratchFailure(object):

    def __init__(self, message):
        self.message = message


class ScratchHome(object):

    def __init__(self, realm, compartment, user):
        self.realm = realm
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
        if self.compartment:
            result = "ScratchHome: `" + self.absolute_path + \
                "' in compartment `" + \
                self.compartment.short_name + "'."
        else:
            result = "ScratchHome: `" + self.absolute_path + \
                "' (not in a compartment)"

        return result


class ScratchCompartment(object):

    def __init__(self, short_name, regex=None):
        self.regex = regex
        self.short_name = short_name
        self.realms = []

    def __key(self):
        return (self.regex, self.short_name)

    def __eq__(x, y):
        return x.__key() == y.__key()

    def __hash__(self):
        return hash(self.__key())

    def __repr__(self):
        result = "ScratchCompartment: `" + self.short_name + "'."
        return result

# EOF
