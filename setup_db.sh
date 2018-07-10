#!/usr/bin/env bash

# Nos aseguramos de que el script se corra como root
if [ "$(id -u)" != "0" ]; then
   echo "Este script debe correrse root" 1>&2
   exit 1
fi

export LC_ALL='es_AR.UTF-8'
export LANGUAGE='es_AR.UTF-8'
export LANG='es_AR.UTF-8'

for i in "$@"
do
case $i in
    -c=*|--cluster=*)
    cluster="${i#*=}"
    ;;
    -d=*|--dbname=*)
    dbname="${i#*=}"
    ;;
    -u=*|--dbuser=*)
    dbuser="${i#*=}"
    ;;
    -p=*|--dbpass=*)
    dbpass="${i#*=}"
    ;;
    *)
            # unknown option
    ;;
esac
done

if [ -z "$dbname" ]; then dbname='mapground'; fi
if [ -z "$dbuser" ]; then dbuser='mapground'; fi

if [ -z "$dbpass" ]; then
read -s -p "Ingrese el password para asignar al usuario de la base de datos:" dbpass;
echo;
fi

if ! [ -z "$cluster"]; then
echo "Creating cluster on '$cluster'...";
pg_dropcluster 10 main --stop
pg_createcluster -d $cluster --start-conf auto 10 main --start
fi

echo "Creando base '$dbname' con usuario '$dbuser'..."

sudo -u postgres bash -c "dropdb $dbname; dropuser $dbuser" 2>/dev/null
sudo -u postgres bash -c "createuser -s $dbuser"
service postgresql restart
sudo -u postgres bash -c "createdb -l es_AR.utf8 -O $dbuser -T template0 $dbname"
sudo -u postgres psql -d $dbname < setup.sql
sudo -u postgres psql -d $dbname -c "alter user $dbuser with password '$dbpass'; create schema data; alter schema data owner to $dbuser; alter schema utils OWNER TO $dbuser;ALTER FUNCTION utils.campos_de_tabla(character varying, character varying) OWNER TO $dbuser;"
