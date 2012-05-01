; ========================================================================
;
;        A sample hypnotoad configuration file for the red network.
;
; ========================================================================

; ========================================================================
; Basic options for hypnotoad.
; ========================================================================
[Basic Options]
state_dir:                     /tmp/hypnotoad
lock_file_name:                /tmp/hypnotoad/lock
plugins_dir:                   plugins

; ========================================================================
; Options for data model (input) plugins.
; ========================================================================
[Data Model Options]

; Options for the LANL HPC LDAP plugin.
ldap_plugin_enabled:           no
ldap_server:                   ldap://bear.lanl.gov
ldap_timeout:                  30
ldap_dc:                       DC=rry,DC=hpc,DC=lanl,DC=gov
ldap_ou_group:                 drm-group
ldap_ou_user:                  user


; Options for the old LANL HPC LDAP plugin.
oldldap_plugin_enabled:        yes
oldldap_server:                ldap://hpcldap.lanl.gov
oldldap_timeout:               30
oldldap_dc:                    DC=hpc,DC=lanl,DC=gov
oldldap_group_ou:              group-ou-not-used
oldldap_use_groups:            no  ; collect group data (expensive)

; This is a nested structure of compartments that contain OUs which contain
; users of that compartment.
oldldap_user_compartment_ous:  {"asc": [ "nfs.lanl.gov" ] }

; ========================================================================
; Options for action (output) plugins.
; ========================================================================
[Action Options]

; Options for the Moab scheduler plugin.
moab_plugin_enabled:           no
moab_case_sensitive:           no   ; for compatibility

; Options for the Slurm scheduler plugin.
slurm_plugin_enabled:          no

; Options for the passwd file generator plugin.
passwd_file_plugin_enabled:    no

; Options for the Panasas links plugin.
panlinks_plugin_enabled:       yes
panlinks_mount_point:          /panfs ; the root mount point for PanFS
panlinks_skip_bad_realms:      no     ; skip realms that time out
panlinks_max_diff_count:       10     ; max diff from the previous run
panlinks_new_dir_perms:        0700   ; permissions for new directories
panlinks_max_skip_bad_vols:    3      ; max number of bad volumes to skip
panlinks_max_skip_bad_realms:  1      ; max number of bad realms to skip
panlinks_subprocess_timeout:   4      ; max seconds to wait for a subprocess
panlinks_pristine_dir_create:  yes    ; should we create a pristine directory
panlinks_pristine_mount_dir:   /usr/projects ; the root mount point for pristine
panlinks_pristine_subdir:      systems/links ; the subdir for pristine
panlinks_skip_realms:          all-realms-active ; comma seperated list of realms to skip

; This is a list of options for each compartment. "vol_regex" is a regular
; expression to match on a volume list in each realm. "symlink_prefix" is
; the prefix to be used for symlink creation to each volume's user directories.
panlinks_compartment_options:  { "asc":
                                 {
                                   "vol_regex": "/(^vol\\d{1,}$)/ix",
                                 }
                               }

; ================================ EOF ===================================
