#
# Base classes for use in the lustredirs action.
#

class ScratchUser(object):
    def __init__(self, short_name, uid="-1", gid="-1"):
        self.short_name = short_name
        self.uid = uid
        self.gid = gid
        self.homes = []

class ScratchRealm(object):
    def __init__(self, base_name):
        self.users = []
        self.failures = []
        self.base_name = base_name
        self.absolute_path = None
        self.containing_path = None
        self.has_failed = False

class ScratchFailure(object):
    def __init__(self, message):
        self.message = message

class ScratchHome(object):
    def __init__(self, realm, user):
        self.realm = realm
        self.user = user
        self.absolute_path = None

    def __key(self):
        return (self.absolute_path)

    def __eq__(x, y):
        return x.__key() == y.__key()

    def __hash__(self):
        return hash(self.__key())

    def __repr__(self):
        result = "ScratchHome: `" + self.absolute_path + "'."
        return result

# EOF
