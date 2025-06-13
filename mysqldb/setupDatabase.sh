#!/bin/bash

mysql $@ < 00-setup.sql

mysql $@ -D Auth_service < 01-createUserTable.sql
mysql $@ -D Auth_service < 02-createDeviceTable.sql
mysql $@ -D Auth_service < 03-createServiceTable.sql
mysql $@ -D Auth_service < 04-createUserServiceTable.sql
mysql $@ -D Auth_service < 05-addRoles.sql
mysql $@ -D Auth_service < 06-addUsers.sql
