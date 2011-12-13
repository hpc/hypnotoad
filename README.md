hypnotoad
=========
A utility that aids in transporting user and priority information to a scheduler on a cluster.

Design Overview
---------------
A user runs hypnotoad specifying a data source and output. The data source is currently limited to ldap, but there's no reason why it couldn't be a database server or another storage location of user and priority information somewhere. See the documentation included with datasource.py for more information on creating a new data source type. After a data source is specified, the data is passed to scheduler.py. scheduler.py is an abstraction for outputing to a specific scheduler's configuration file format. Currenly, only moab is supported. See scheduler.py and the moab.py scheduler plugin as an example of how to create output for a different scheduler type.
