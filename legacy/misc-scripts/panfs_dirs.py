#!/usr/bin/python

# 1. Check hostname and root user. Bail if not FTA and root.
# 2. Get list of LDAP users, vol count, and compare to current list on fs.
#    Bail if nothing to do. Bail on LDAP or fs errors.
# 3. Create users, using lowest vol count dirs first

# Load modules
import socket
import sys
import subprocess
import os
import re
import glob
import ldap
import datetime
import time
import signal
import logging
from optparse import OptionParser
from operator import itemgetter

#
# General Set up 

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

# Options
parser = OptionParser()
parser.add_option("-v", "--verbose",
                      action="store_true", dest="verbose_opt", default=False,
                      help="print step by step processing information")

(options, args) = parser.parse_args()
VERBOSE = options.verbose_opt

# -------------------------------------------------
def main():
    
    # Check for proper environment to run, returns mounted panasas realms
    mounted_panfs_list, panfs_dirs = \
    check_env()
    
    # Returns a list of current users with existing directories
    # a list of scratch directories,  and a count of directories per volume
    d_realm_vol_users = \
    get_panfs_info(mounted_panfs_list, panfs_dirs)
   
    # Returns a list of all users from LDAP, with info 
    d_ldap_users = \
    get_ldap_users()
  
    # Find anomalies in user info (Duplicate/Legacy/Invalid named), create useful lists of users
    all_current_users, all_legacy_users, all_dupe_users, d_realm_vol_counts, d_realm_dupe_user_vols, \
    d_realm_vol_legacy_users, d_realm_vol_invalid_users = \
    panfs_info_integrity(d_realm_vol_users, d_ldap_users)
   
    # Returns a dictionary of all NEW users, with info 
    d_new_users = \
    gen_new_users(d_ldap_users, all_current_users)
   
    # Creates new directories for new users 
    d_realm_vol_created_users = \
    create_new_pan_dirs(d_new_users, panfs_dirs, d_realm_vol_counts)
  
    # Create symlinks for current, valid users and new users
    create_pan_symlinks(d_realm_vol_created_users, d_realm_vol_users, all_current_users, all_dupe_users, all_legacy_users)

    # Report anomalies
    report_errata(d_realm_dupe_user_vols, d_realm_vol_legacy_users, d_realm_vol_invalid_users, d_ldap_users)
 
# --------------------------------------------------  

def verbose(msg):
    # We use stdout.write instead of print so we can control the trailing line return 
    if VERBOSE:
        sys.stdout.write(msg)
    else:
        pass
# --------------------------------------------------

def check_env():
    # Check for expected hostnames

    # Check for user=root

    # Check for mounted Panasas
    panfs_dirs = []
    mounted_panfs_list = []
    notmounted_panfs_list = []
   
    # Get list of scratch directories(mount points) 
   
    # Per the fstab file
    # Example fstab line:  panfs://10.1.202.161/         /panfs/scratch2 panfs ...
    try:    
        panfs_mnt_pat = re.compile('^panfs://[0-9.]+/\s+(/panfs/scratch[0-9]*) panfs.*')
        f = open("/etc/fstab")
        for line in f:
            m_fstab = panfs_mnt_pat.match(line)
            if m_fstab:
                m = re.search('(?<='+panfs_mnt_root+').*', m_fstab.group(1))
                panfs_dirs.append(m.group(0))
    except: 
        print "Error reading the fstab file - no panfs directories found"
        sys.exit()
   
    panfs_dirs = sorted(panfs_dirs)
    for dir in panfs_dirs:
        check_mounted_panfs_cmd = "/bin/mount -t panfs | grep " + dir
        command_return_status, command_return_stdout, command_return_stderr = \
        timeout_command(check_mounted_panfs_cmd, shell_cmd_timeout)
        if command_return_status == 0:
            mounted_panfs_list.append(dir)
        else:
            notmounted_panfs_list.append(dir)
    if len(notmounted_panfs_list) != 0:
        print "Error: The following configured Panasas filesystems are\
               currently NOT Mounted:"
        print notmounted_panfs_list
        print "Exiting..."
        sys.exit()

    if len(panfs_dirs) == len(mounted_panfs_list):
        # All with mount points = mounted
        verbose("All Panasas filesystems are mounted\n")
        return (mounted_panfs_list, panfs_dirs)
# --------------------------------------------------

def get_panfs_info(mounted_panfs_list, panfs_dirs):
    vol_list = []
    fstab_panfs_mnts = []
    
    d_realm_vol_users = {}
   
        # Get a count of user directories under each vol space
        # We will use that sorted list to create new directories
        # from least populated up...
        
    for realm in mounted_panfs_list:
        d_vol_users = {}
       
        # Compose our shell command to return the list of volumes in each realm 
        find_vols_cmd = "find " + panfs_mnt_root + realm + " -maxdepth 1 -name vol* -printf \"%f \""
        
        # Get the list of volumes for each realm (in timeout loop)
        try:
            command_return_status, command_return_stdout, command_return_stderr = \
            timeout_command(find_vols_cmd, shell_cmd_timeout)
            if command_return_status == 0:
                vol_list = command_return_stdout.split()
            else:
                print command_return_stderr
                sys.exit()
        except Exception, e:
            print e
        
        for vol in vol_list:
            # Compose our shell command to return the list of user dirs in each volume
            find_user_dirs_cmd = "find " + panfs_mnt_root + realm + "/" + vol + " -maxdepth 1 -mindepth 1 -type d ! -name Lost+Found* -printf \"%f \""
            
            # Get the list of user dirs for each volume (in timeout loop)
            try:
                command_return_status, command_return_stdout, command_return_stderr = \
                timeout_command(find_user_dirs_cmd, shell_cmd_timeout)
                if command_return_status == 0:
                    vol_user_dirs = command_return_stdout.split()
                else:
                    print command_return_stderr
                    sys.exit()
            except Exception, e:
                print e
            d_vol_users[vol] = vol_user_dirs
            # End of vol loop 
        # Create a nested dictionary of realms and their associated volume counts
        d_realm_vol_users[realm] = d_vol_users
    
    # End of realm loop
    return(d_realm_vol_users)

# --------------------------------------------------  

def get_net():
    # Define network partition <-> IP matches
    yell_pat = re.compile(r"128\.165\.\d+\.\d+")
    turq_pat = re.compile(r"204\.121\.6[45]+\.\d+")
    red_pat =  re.compile(r"10\.\d+\.\d+\.\d+")

    p1 = subprocess.Popen(["ifconfig"], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["grep", "inet "], stdin=p1.stdout, stdout=subprocess.PIPE)
    p3 = subprocess.Popen(["awk", '{print $2}'], stdin=p2.stdout, stdout=subprocess.PIPE)
    intf_ip_list = p3.communicate()[0]
 
    if re.search(yell_pat, intf_ip_list):
        server = yell_ldap_server
        ldap_ou = yell_ldap_ou
    elif re.search(turq_pat, intf_ip_list):
        server = turq_ldap_server
        ldap_ou = turq_ldap_ou
    elif re.search(red_pat, intf_ip_list):
        server = red_ldap_server
        ldap_ou = red_ldap_ou
    else:
        print "Could not determine the network partition from current configured interfaces."
        sys.exit()
    if len(server) > 0:
        return server,ldap_ou

# --------------------------------------------------  

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

def create_new_pan_dirs(d_new_users, panfs_dirs, d_realm_vol_counts, ):
    d_realm_vol_created_users = {}
    if  len(d_new_users) > 0:
        new_users = d_new_users.keys()
        for realm in d_realm_vol_counts.keys():
            d_vol_created_users = {}
            for user in new_users:
                l_user_info = d_new_users[user]
                user_uid = l_user_info[0]
                user_gid = l_user_info[1]

                # Sort volumes by directory count. Lowest count volume is where we write the new user dir
                # Increment and then resort after each new user is added successfully

                # Sort
                d_realm_vols = d_realm_vol_counts[realm]
                realm_vols_ascending = sorted(d_realm_vols.items(), key=itemgetter(1))

                # Here is the volume in this realm that we will create the new user's directory
                # [0] <- realm, [0] <- lowest count volume after sort
                vol_to_write = panfs_mnt_root + realm + "/" + realm_vols_ascending[0][0]

                # Prepare system commands to execute
                new_user_dir = vol_to_write + "/" + user
                mkdir_command = "mkdir " + new_user_dir
                chown_command = "chown " + user_uid + ":" + user_gid + " " + new_user_dir
                chmod_command = "chmod " + str(new_dir_perms) + " " + new_user_dir
                dir_create_cmd = mkdir_command + ";" + chown_command + ";" + chmod_command

                #dir_create_cmd = "/users/sweatt/sleeper.sh"  # Test

                # Write/Increment
                verbose("Creating directory for user \"" + user + "\" : " + new_user_dir + " ... ")
                try:
                    command_return_status, command_return_stdout, command_return_stderr = \
                    timeout_command(dir_create_cmd, shell_cmd_timeout)
                    if command_return_status == 0:
                        verbose("success\n")
                        verbose("   " + chown_command + "\n")
                        verbose("   " + chmod_command + "\n")
                        
                        vol = realm_vols_ascending[0][0]
                       
                        if vol in d_vol_created_users.keys():
                            created_users = d_vol_created_users[vol]
                            created_users = created_users.append(user)
                            d_vol_created_users[vol] = created_users
                        else:
                            d_vol_created_users[vol] = user
                    else:
                        print command_return_stderr
                        sys.exit()
                     
                except Exception, e:
                    print e
                d_realm_vol_counts[realm][realm_vols_ascending[0][0]] +=1
            d_realm_vol_created_users[realm] = d_vol_created_users
    return d_realm_vol_created_users
# --------------------------------------------------

def create_pan_symlinks(d_realm_vol_created_users, d_realm_vol_users, all_current_users, all_dupe_users, all_legacy_users):
    # Create symlinks for all directories as needed
    
    # Create existing symlinks if missing
    for realm in d_realm_vol_users.keys():
        realm_current_symlinks = []
        for vol in d_realm_vol_users[realm]:
            for user in d_realm_vol_users[realm][vol]:
                if (user in all_current_users and user not in all_dupe_users and user not in all_legacy_users): 
                    print "Creating symlink: /panfs/" + realm + "/" + vol + "/" + user
                    realm_current_symlinks.append(user)
                else:
                    print "Not creating symlink for: " + user
            
    print str(len(realm_current_symlinks))
    # Create new user symlinks
    print "New user info: " + str(d_realm_vol_created_users)
# --------------------------------------------------

def timeout_command(command, timeout):
# Call shell-command and either return its output or kill it
# if it doesn't normally exit within timeout seconds and return None
    cmd = command
    start = datetime.datetime.now()
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    while process.poll() is None:
        time.sleep(0.5)
        now = datetime.datetime.now()
        if (now - start).seconds > timeout:
            os.kill(process.pid, signal.SIGTERM)
            os.waitpid(-1, os.WNOHANG)
            
            # We set our return status and stderr values since our process can't return diddly
            stderr = "Command timed out: " + str(cmd)
            status = 2
            return status, '', stderr
    
    # Process completed. Return process values
    status = process.returncode
    stdout = process.stdout.read()
    stderr = process.stderr.read()
    return status, stdout, stderr
# --------------------------------------------------

def report_errata(d_realm_dupe_user_vols, d_realm_vol_legacy_users, d_realm_vol_invalid_users, d_ldap_users):
    verbose("Duplicate users found in realm: " + str(d_realm_dupe_user_vols) + "\n")
    verbose("Invalid usernames found in realm: " + str(d_realm_vol_invalid_users) + "\n")

####################### MAIN #######################
if __name__ == "__main__":
    main()
