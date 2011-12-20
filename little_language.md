Scheduler Little Language v0.1
==============================
This file is a draft of the attributes contained in the data that datamodel
plugins will send to scheduler plugins. This document is subject to drastically
change as the initial model is implemented. Relationships between bullet points
and sub-bullet points are simply nested dictionaries with no cycles allowed.

The prefered method for serializing this data format is JSON.

* model_entry
  * little_lang_entry                   # entries specific to the little language version
    * version_integer                   # the version number of the lanugage protocol

  * enterprise_entry                    # entries specific to the enterprise
    * enterprise_string                 # the enterprise name (i.e. Dept. of Energy)
    * organization_string               # the organization name (i.e. LANL)
    * group_string                      # the group name (i.e. HPC-3)
    * responsible_party_string          # the owner name (i.e. Jon Bringhurst)

  * cluster_entry                       # specific to the cluster
    * short_code_string                 # the node prefix (i.e. tu)
    * long_name_string                  # the long name (i.e. turing)
    * scheduler_type_string             # the type of scheduler (i.e. moab/slurm)
    * location_campus_string            # the campus location (i.e. Los Alamos)
    * location_building_string          # the building name (i.e. LDCC)
    * location_room_string              # the room number (i.e. 205)

  * group_entry                         # specific to groups on the cluster
    * short_name_string
    * user_member_short_name_array
    * group_member_short_name_array
    * group_id_integer
    * priority_fairshare_float
    * priority_qos_name_array

  * user_entry                          # specific to users on the cluster
    * short_name_string
    * full_name_string
    * group_id_integer
    * user_id_integer
    * home_directory_string
    * full_name_string
    * login_shell_string
    * priority_age_float
    * priority_fairshare_float
    * priority_jobsize_float
    * priority_partition_float
    * priority_qos_name_array
