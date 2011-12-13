import getopt, sys

def load_plugin(path, cls, name):
    """
    Find the first subclass of cls with name in py files located below path
    (does look in sub directories)
 
    @param path: the path to the top level folder to walk
    @type path: str
    @param cls: the base class that the subclass should inherit from
    @type cls: class
    @param name: the name of the class
    @param name: str
    @rtype: class
    @return: the first class found which is a subclass of cls with name
    """
 
    def look_for_subclass(modulename):
        log.debug("Searching %s" % (modulename))
        module=__import__(modulename)
 
        #walk the dictionaries to get to the last one
        d=module.__dict__
        for m in modulename.split('.')[1:]:
            d=d[m].__dict__
 
        #look through this dictionary for things
        #that are subclass of Job
        #but are not Job itself
        for key, entry in d.items():
            if key == cls.__name__:
                continue
 
            try:
                if issubclass(entry, cls) and name == modulename:
                    log.debug("Found plugin:" + key)
                    return entry
            except TypeError:
                #this happens when a non-type is passed in to issubclass. We
                #don't care as it can't be a subclass of Job if it isn't a
                #type
                continue
 
    for root, dirs, files in os.walk(path):
        for name in files:
            if name.endswith(".py") and not name.startswith("__"):
                path = os.path.join(root, name)
                modulename = path.rsplit('.', 1)[0].replace('/', '.')
                look_for_subclass(modulename)

    # We didn't find anything if we get here.
    return None


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "vhc:", ["help", "config="])
    except getopt.GetoptError, err:
        print str(err)
        usage()
        sys.exit(2)
    output = None
    verbose = False
    for o, a in opts:
        if o == "-v":
            verbose = True
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-c", "--config"):
            # do something
        else:
            assert False, "unhandled option"

if __name__ == "__main__":
    main()
