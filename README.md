hypnotoad
=========
A utility that aids in transporting user and priority information from one or
more data sources to various applications on a cluster.

Design Overview
---------------
A user runs hypnotoad specifying a data model type and action output type
along with options specific to the data model and action type.

The data model is currently limited to ldap, but there's no reason why it
couldn't be replaced or amended with a database server or another storage
location of user and priority information somewhere. See the documentation
included with datamodel.py for more information on creating a new data model
type.

After one or more data models are specified, the data is passed to action.py.
action.py is an abstraction for outputing to a specific application based on
that application's requirements. See action.py and the moab_plugin.py action
plugin as an example of how to create action plugins for various applications.

Hypnotoad Little Language
-------------------------
This is a draft of the attributes contained in the data that datamodel plugins
will send to action plugins. This document is subject to drastically change
as the initial model is implemented. Relationships between bullet points and
sub-bullet points are simply nested dictionaries with no cycles allowed.

Every field is optional in the data model. However, plugins may choose to ignore
model entries (with an option for warning an administrator) if the data is
incomplete or invalid.

The prefered method for serializing this data format is JSON.

* model_entry
  * little_lang_entry                # entries specific to the little language version
    * version_integer                # version number of the lanugage protocol

  * enterprise_entry                 # entries specific to the enterprise
    * enterprise_string              # enterprise name (i.e. Dept. of Energy)
    * organization_string            # organization name (i.e. LANL)
    * group_string                   # group name (i.e. HPC-3)
    * responsible_party_string       # owner name (i.e. Jon Bringhurst)

  * cluster_entry                    # specific to the cluster
    * short_code_string              # node prefix (i.e. tu)
    * long_name_string               # long name (i.e. turing)
    * location_campus_string         # campus location (i.e. Los Alamos)
    * location_building_string       # building name (i.e. LDCC)
    * location_room_string           # room number (i.e. 205)
    * fairshare_halflife_float       # fairshare decay factor
    * fairshare_interval_float       # fairshare window size
    * fairshare_depth_float          # fairshare depth size
    * priority_weight_age            # weight to place on job age
    * priority_weight_fairshare      # weight to place on fairshare calculation
    * priority_weight_job_size       # weight to place on job size
    * priority_weight_partition      # weight to place on job location
    * priority_weight_qos            # weight to place on QOS
    
  * group_entry                      # specific to groups on the cluster
    * short_name_string              # unix short-name of the group
    * user_member_short_name_array   # unix short-names of users in this group
    * group_member_short_name_array  # unix short-names of groups in this group (non-cyclic)
    * group_id_integer               # unix gid of this group
    * priority_fairshare_float       # fairshare priority target
    * priority_qos_name_array        # qos available to this group

  * user_entry                       # specific to users on the cluster
    * short_name_string              # unix short name of this user
    * full_name_string               # the full name of this user
    * group_short_name_string        # this users default unix group short-name
    * user_id_integer                # the unix uid of this user
    * home_directory_string          # the home directory of this user
    * login_shell_string             # the login shell for this user
    * priority_fairshare_float       # fairshare priority target
    * priority_qos_name_array        # qos available to this user

# EOF
