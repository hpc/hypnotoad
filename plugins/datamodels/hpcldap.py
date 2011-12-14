#
# An ldap data model plugin for hypnotoad.
#

from hypnotoad import plugin
import ldap
import logging

LOG = logging.getLogger('root')

class hpcldap(plugin.data_model_plugin):
    def setup(self, config):
        """Called before the plugin is asked to do anything."""
        LOG.debug("Got to hpcldap setup")

        if config.getboolean('Data Model Options', 'ldap_plugin_enabled'):
            LOG.debug("hpcldap plugin enabled")

        self.config = config

    def teardown(self):
        """Called to allow the plugin to free anything."""
        LOG.debug("Got to hpcldap teardown")

    def user_info(self):
        """Look up user information in this data model."""
        LOG.debug("Got to hpcldap user_info")

    def priority_info(self):
        """Look up priority information in this data model."""
        LOG.debug("Got to hpcldap priority_info")
"""

# Globals
dc = "DC=hpc,DC=lanl,DC=gov"
panfs_mnt_root = '/panfs/'
shell_cmd_timeout = 30
new_dir_perms = 700

# LDAP settings
yell_ldap_server = "ldap://hpcldap.lanl.gov"
yell_ldap_ou="scratch"

turq_ldap_server = "ldap://turq-accts.lanl.gov"
turq_ldap_ou="scratch"

red_ladp_server = "ldap://hpcldap.lanl.gov"
red_ldap_ou="nfs"

def get_ldap_users():
    d_ldap_users = {}
    d_valid_users = {}
    d_invalid_users = {}
    
    server,ldap_ou = get_net()
    dn = "ou=" + ldap_ou + ",DC=hpc, DC=lanl, DC=gov" 

    verbose("Connecting to: " + server + " ... ")
    try:
        l=ldap.initialize(server)
        l.simple_bind_s()
        verbose("success\n")
    except Exception, e:
        print "\nCannot connect to server: " + server
        print "Reason: " + str(e) + "\n"
        sys.exit()
    
    verbose("  Selecting all users in with OU = " +  ldap_ou + " ... ")

    try:
        for ldap_line in l.search_s(
            dn ,
            ldap.SCOPE_SUBTREE,
            "(uid=*)",
            ['cn', 'loginShell', 'uidNumber', 'gidNumber', 'gecos', 'homeDirectory', 'uid'],
            ):

            # A sample of a line returned from the LDAP search (ldap_line):
            # The order can vary. :(
            # ('uid=scowell,ou=nfs.lanl.gov,dc=hpc,dc=lanl,dc=gov', {'cn': ['Shannon T. Holloway'], 'loginShell': ['/bin/tcsh'], 'uidNumber': ['25142'], 'gidNumber': ['25142'], 'gecos': ['Shannon T. Holloway,185688'], 'homeDirectory': ['/users/scowell'], 'uid': ['scowell']})
            
            # We parse out the set of values from the returned LDAP line string
            ldap_line = str(ldap_line) 
            # Set up matching patterns
            ldap_line_dn_pat = '\(\'uid=.*,ou=.*,dc=.*, {'
            ldap_line_end_pat = r'}\)' 
            ldap_line_pat = re.compile(ldap_line_dn_pat + "(.*)" + ldap_line_end_pat)
           
 
            # Patterns for all of the data fields. It was found that the order of the fields could vary
            # To allow for random order or fields - each field is parsed separately. Sorry.

            field_pat = '\': \[(?:\'|\")(.+?)(?:\'|\")'
            
            uid_pat = re.compile('uid' + field_pat)
            cn_pat = re.compile('cn' + field_pat)
            loginShell_pat = re.compile('loginShell' + field_pat)
            uidNumber_pat = re.compile('uidNumber' + field_pat)
            gidNumber_pat = re.compile('gidNumber' + field_pat)
            gecos_pat = re.compile('gecos' + field_pat)
            homeDirectory_pat = re.compile('homeDirectory' + field_pat)
            
            ldap_line_string = re.match(ldap_line_pat, ldap_line)
            if ldap_line_string:
                # Here we get the final values and change them to
                # names we are used to
                ldap_values_string = ldap_line_string.group(1)
                try:
                    moniker = uid_pat.search(ldap_values_string).group(1)
                    name = cn_pat.search(ldap_values_string).group(1)
                    shell = loginShell_pat.search(ldap_values_string).group(1)
                    uid = uidNumber_pat.search(ldap_values_string).group(1)
                    gid = gidNumber_pat.search(ldap_values_string).group(1)
                    gecos = gecos_pat.search(ldap_values_string).group(1)
                    homedir = homeDirectory_pat.search(ldap_values_string).group(1)
                   
                    # Time to put values into a dictionary for processing later.
                    # Key = moniker (unique), Value = A list of all other values 
                    
                    # Check for valid shell. Skip if not valid
                    # Valid shells: bash, tcsh, rssh, csh, ksh, zsh, sh
                    if re.match(r"(/usr)*/s*bin/(ba|tc|rs|c|k|z)sh", shell):
                    
                        # Time to put values into a dictionary for processing later.
                        # Key = moniker (unique), Value = A list of all other values
                        ldap_user_values = [uid, gid, homedir, gecos, name, shell]
                        d_ldap_users[moniker] = ldap_user_values
                    else:
                        print "User has invalid shell: " + shell
                
                except:
                    print "Could not process the following LDAP line:\n"
                    print ldap_line
        verbose("success\n")
    except Exception, e:
        print "LDAP search error"
        print e
        sys.exit()
        #if len(d_invalid_users) > 0:
            #print "Invalid shells for users: " + d_invalid_users
    ldap_users_count = len(d_ldap_users) 
    verbose("LDAP user count: " + str(ldap_users_count) + "\n")
    if ldap_users_count == 0:
        print "LDAP search returned 0 users"
        sys.exit()

    # Add fake new users for testing.. :)
    #d_ldap_users['bogus1'] = '99999', '99999', '/users/bogus1', 'Bogus S. Fake,199100', 'Bogus S. Fake', '/bin/tcsh'
    #d_ldap_users['scammer'] = '88888', '88888', '/users/scammer', 'Scammer Q. Pfft,123456', 'Scammer Q. Pfft', '/bin/bash'
    
    return d_ldap_users 
   
# --------------------------------------------------
 
def gen_new_users(d_ldap_users, all_current_users):
    l_new_users = []
    l_old_users = []
    d_new_users = {}
    
    # Build list of new users (In LDAP but have no current panfs directory)
    for key in sorted(d_ldap_users.keys()):
        if str(key) not in all_current_users:
             l_new_users.append(str(key))
    for user in all_current_users:
        if user not in d_ldap_users.keys():
             l_old_users.append(user)
    
    if len(l_new_users) > 0:
        verbose("New users to be added: " + str(l_new_users) + "\n")
        for user in l_new_users:
            l_new_user_info = d_ldap_users[user]
            d_new_users[user] = l_new_user_info
    return d_new_users
# -------------------------------------------------- 

def panfs_info_integrity(d_realm_vol_users, d_ldap_users):

    all_realm_users = []
    all_ldap_users = []
    all_legacy_users = []
    all_dupe_users = []
    du_users = []
    le_users = []
    d_realm_vol_counts = {}
    d_realm_vol_valid_users = {}
    d_realm_users = {}
    d_realm_dupe_user_vols = {}
    d_realm_users_vols = {}
    d_realm_vol_legacy_users = {}
    d_realm_vol_invalid_users = {}
    valid_username_exp = "\w+$"
    
    # Extract reduced dictionaries that represent:
      # Users per realm - to determine:
        # Duplicate users in a realm
        # Missing users in a realm
        # Create a master list of all unique users
        # Count of users per volume in a realm - to determine:
        # Where to create new user directories (lowest first)

    # Create a list of all LDAP users
    all_ldap_users = d_ldap_users.keys()
 
    for realm in d_realm_vol_users.keys():
        realm_users = []
        dupe_users = []
        d_vol_valid_users = {}
        d_vol_users_clean = {}
        d_vol_users = {}
        d_vol_counts = {}
        d_vol_legacy_users = {}
        d_vol_invalid_users = {}

        for vol in d_realm_vol_users[realm].keys():
            vol_invalid_users = []
            vol_valid_users = []
            legacy_users = []
           
            # Create lists of legacy/defunct users & invalid named "users" 
            # We have to find the dupe users, then create
            # the dict later
            for user in d_realm_vol_users[realm][vol]:
                    if re.match(valid_username_exp, user):
                        vol_valid_users.append(user)
                        if user not in realm_users: 
                            realm_users.append(user)
                        else:
                            if user not in dupe_users:
                                dupe_users.append(user)
                        if user not in all_ldap_users:
                            legacy_users.append(user)
                    else:
                        vol_invalid_users.append(user)

            # Put the rogue lists into volume dictionaries
            # Get volume counts - we are NOT counting invalid named directories
            d_vol_valid_users[vol] = vol_valid_users
            if vol_invalid_users:
                d_vol_invalid_users[vol] = vol_invalid_users
            d_vol_legacy_users[vol] = legacy_users
            
            # Volume counts
            d_vol_counts[vol] = len(d_vol_valid_users[vol])
        # Now we cycle through all valid users and create a user-based dict
        # with dupicate volume directories (dupes)
        d_dupe_user_vols = {}
        for vol in d_realm_vol_users[realm].keys():
            for user in d_realm_vol_users[realm][vol]:
                if re.match(valid_username_exp, user): 
                    if (user in dupe_users and user in d_dupe_user_vols.keys()):
                        user_dupe_vol = d_dupe_user_vols[user]
                        user_dupe_vol.append(vol)
                        d_dupe_user_vols[user] = user_dupe_vol
                    elif (user in dupe_users and user not in d_dupe_user_vols.keys()):
                        d_dupe_user_vols[user] = [vol]

        d_realm_users[realm] = realm_users 
        d_realm_vol_valid_users[realm] = d_vol_valid_users
        d_realm_vol_legacy_users[realm] = d_vol_legacy_users
        
        if d_vol_invalid_users:
            d_realm_vol_invalid_users[realm] = d_vol_invalid_users
        if d_dupe_user_vols:
            d_realm_dupe_user_vols[realm] = d_dupe_user_vols
        d_realm_vol_counts[realm] = d_vol_counts
        print len(d_ldap_users.keys())
        print d_realm_dupe_user_vols
        print "\n"
        try:
            print d_realm_vol_invalid_users[realm]
        except:
            pass
        if d_realm_vol_legacy_users[realm]:
            print "\nLegacy users: " + str(realm) + ": "
            print d_realm_vol_legacy_users[realm]
        print "\n"

    # Create list of all unique, current users
    for realm in d_realm_users.keys():
        all_realm_users.extend(d_realm_users[realm]) 
        
    # Create list of all unique legacy users
    for realm in d_realm_vol_legacy_users.keys():
        for vol in d_realm_vol_legacy_users[realm].keys():
            for le_user in d_realm_vol_legacy_users[realm][vol]:
                le_users.append(le_user)

        # Create a list of all unique dupe users
    for realm in d_realm_dupe_user_vols.keys():
        for du_user in d_realm_dupe_user_vols[realm].keys():
            du_users.append(du_user)

    all_current_users = set(all_realm_users)
    all_legacy_users = set(le_users)
    all_dupe_users = set(du_users)

     
    return (all_current_users, all_legacy_users, all_dupe_users, d_realm_vol_counts, d_realm_dupe_user_vols, d_realm_vol_legacy_users, d_realm_vol_invalid_users)
# --------------------------------------------------

    verbose("Duplicate users found in realm: " + str(d_realm_dupe_user_vols) + "\n")
    verbose("Invalid usernames found in realm: " + str(d_realm_vol_invalid_users) + "\n")

"""
