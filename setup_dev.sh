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

if [ -z "$dbname" ]; then dbname='mapground_dev'; echo "Base de datos por defecto: $dbname"; fi
if [ -z "$dbuser" ]; then dbuser='mapground_dev'; echo "Usuario de base de datos por defecto: $dbuser"; fi

echo "Configurando base de datos en localhost...";

if [ -z "$dbpass" ]; then
  read -s -p "Ingrese el password para asignar al usuario de la base de datos:" dbpass;
  echo;
fi

./setup_db.sh -d=$dbname -u=$dbuser -p=$dbpass ;

SECRET_KEY=$(python mk_secret_key.py)

DIR="$( cd "$(dirname "$0")" ; pwd -P )"

DEV_USER="$(ls -ld $0 | awk '{print $3}')"

sed -e "s/mapground-db/${dbname}/g" MapGround/settings_db.py.template | sed -e "s/mapground-user/${dbname}/g" - | sed -e "s/mapground-password/${dbpass}/g" - | sed -e "s/secret-key/${SECRET_KEY}/g" > MapGround/settings_dev_db.py
cp MapGround/settings_local.py.template MapGround/settings_local.py
chown $DEV_USER MapGround/settings_dev_db.py MapGround/settings_local.py

rm -rf /var/cache/mapground_dev 2>/dev/null
rm -rf /var/local/mapground_dev 2>/dev/null

mkdir /var/cache/mapground_dev
mkdir /var/local/mapground_dev
mkdir /var/local/mapground_dev/media
cp -r mapfiles /var/local/mapground_dev
touch /var/local/mapground_dev/mapfiles/map-error.log
chmod 666 /var/local/mapground_dev/mapfiles/map-error.log
cp -r data /var/local/mapground_dev
chown -R $DEV_USER /var/local/mapground_dev
cp mapcache/mapcache.xml.template /var/local/mapground_dev/mapcache.xml
sed -e 's/DEBUG = False$/DEBUG = True/' mapcache/settings.py.template > mapcache/settings.py

sed -e "s:/mapground/:/mapground_dev/:g" mapground_apache.conf.template > /etc/apache2/sites-available/mapground_dev.conf
sed -i "s/^<VirtualHost \*:8080>$/<VirtualHost *:7654>/" /etc/apache2/sites-available/mapground_dev.conf
rm /etc/apache2/sites-enabled/mapground_dev.conf 2>/dev/null
ln -s /etc/apache2/sites-available/mapground_dev.conf /etc/apache2/sites-enabled/mapground_dev.conf

sudo -u ${DEV_USER} bash -c 'virtualenv --system-site-packages venv; source venv/bin/activate; pip install -r requirements.txt'

source venv/bin/activate

./mapcache/manage.py add world_borders
# python manage.py makemigrations
python manage.py migrate
python manage.py loaddata MapGround/fixtures/user.json
python manage.py loaddata layers/fixtures/initial_data.json

deactivate

chown -R www-data:www-data /var/cache/mapground_dev
chmod g+rwxs /var/cache/mapground_dev
chmod 666 /var/local/mapground_dev/mapcache.xml

service apache2 restart
