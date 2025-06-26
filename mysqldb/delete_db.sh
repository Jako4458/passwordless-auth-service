#!/bin/bash

read -p "Are you sure you want to delete database 'Auth_service'? (y/N): " answer
case "$answer" in
    [yY][eE][sS]|[yY])
        ;;
    *)
        echo "Aborted."
        exit 1
        ;;
esac

echo "Dropping database 'Auth_service'..."
mysql $@ -e "DROP DATABASE Auth_service;"

echo "Deleting user 'FlaskAuth'..."
mysql $@ -e "DROP USER IF EXISTS 'FlaskAuth'@'172.18.0.%';"
mysql $@ -e "DROP USER IF EXISTS 'FlaskAuthAdminCLI'@'%';"
mysql $@ -e "DROP ROLE IF EXISTS 'AuthAdmin'@'%';"

