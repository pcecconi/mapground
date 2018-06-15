#!/usr/bin/env bash

apt-get update
apt-get install -y uwsgi apache2 postgresql-9.6-postgis-2.3 python-psycopg2 python-gdal 
service apache2 stop
apt-get install -y nginx python-virtualenv fabric uwsgi uwsgi-plugin-python python-mapscript cgi-mapserver mapserver-bin mapcache-cgi mapcache-tools imagemagick python-lxml curl build-essential libssl-dev python-pip locales
a2enmod cgid
pip install simpleflock
/usr/sbin/locale-gen --purge es_AR.utf8
export LANGUAGE=es_AR.UTF-8
export LANG=es_AR.UTF-8
export LC_ALL=es_AR.UTF-8
dpkg-reconfigure --frontend=noninteractive locales
update-locale LC_CTYPE=es_AR.UTF-8
