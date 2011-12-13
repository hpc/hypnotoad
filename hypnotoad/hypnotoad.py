import getopt, sys

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ho:v", ["help", "output="])
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
        elif o in ("-l", "--ldap-server"):
        elif o in ("-c", "--cache-dir");
        elif o in ("-o", "--log-output-file");
        elif o in ("-e", "--reports-email");
        else:
            assert False, "unhandled option"

if __name__ == "__main__":
    main()
