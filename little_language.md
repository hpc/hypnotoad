# Scheduler Little Language v0.1
# Jon Bringhurst <jonb@lanl.gov>

# This file is a draft of the attributes contained in the data that datamodel
# plugins will send to scheduler plugins. This document is subject to drastically
# change as the initial model is implemented. Relationships between bullet points
# and sub-bullet points are simply nested dictionaries with no cycles allowed.
#
# The prefered method for serializing this data format is JSON.

* model
  * little_lang_entry
    * version_integer
  * enterprise_entry
    * enterprise_string
    * group_string
    * responsible_party_string
  * cluster_entry
    * short_code_string
    * long_name_string
    * location_string
  * group_entry
    * short_name_string
    * user_member_short_name_array
    * group_member_short_name_array
    * group_id_integer
    * priority_fairshare_float
    * priority_qos_name_array
  * user_entry
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

# EOF
