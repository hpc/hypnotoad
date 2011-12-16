hypnotoad
=========
A utility that aids in transporting user and priority information from one or
more data sources to a scheduler on a cluster.

Design Overview
---------------
A user runs hypnotoad specifying a data model type and scheduler output type
along with options specific to the data model and scheduler type.

The data model is currently limited to ldap, but there's no reason why it
couldn't be replaced or amended with a database server or another storage
location of user and priority information somewhere. See the documentation
included with datamodel.py for more information on creating a new data model
type.

After one or more data models are specified, the data is passed to
scheduler.py. scheduler.py is an abstraction for outputing to a specific
scheduler's configuration file format. Currently, only moab is supported. See
scheduler.py and the moab.py scheduler plugin as an example of how to create
output for a different scheduler type.
