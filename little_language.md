This file is a draft of the attributes contained in the data that datamodel
plugins will send to scheduler plugins.

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

* group_entry
  * short_name_string
  * member_short_name_array
  * group_id_integer
  * priority_fairshare_float
  * priority_qos_name_array
