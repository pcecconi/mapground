#!/usr/bin/env bash

apt-get update
apt-get install -y uwsgi apache2 postgresql-9.6-postgis-2.3 postgis
service apache2 stop
apt-get install -y python-psycopg2 python-gdal nginx python-virtualenv fabric uwsgi uwsgi-plugin-python python-mapscript cgi-mapserver mapserver-bin mapcache-cgi mapcache-tools imagemagick python-lxml curl build-essential libssl-dev python-pip locales
a2enmod cgid
rm /etc/apache2/sites-enabled/*
rm /etc/nginx/sites-enabled/default
sed -i 's/^\(Listen\) 80$/\1 8080/' /etc/apache2/ports.conf
sed -i 's/^# *\(es_AR.UTF-8\)/\1/' /etc/locale.gen
pip install simpleflock
/usr/sbin/locale-gen
# dpkg-reconfigure --frontend=noninteractive locales
# update-locale LC_CTYPE=es_AR.UTF-8
