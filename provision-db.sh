#!/usr/bin/env bash

apt-get update
apt-get install -y postgresql-10-postgis-2.4 postgis
/usr/sbin/locale-gen
export LC_ALL=es_AR.UTF-8; export LANGUAGE=es_AR.UTF-8; export LANG=es_AR.UTF-8
dpkg-reconfigure --frontend=noninteractive locales
# update-locale LC_CTYPE=es_AR.UTF-8
