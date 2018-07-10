#!/usr/bin/env bash

# Nos aseguramos de que el script se corra como root
if [ "$(id -u)" != "0" ]; then
   echo "Este script debe correrse root" 1>&2
   exit 1
fi

LOG_DIR='/var/log/mapground'

rm -rf ${LOG_DIR} 2>/dev/null
mkdir ${LOG_DIR}
DIR="$( cd "$(dirname "$0")" ; pwd -P )"
DEV_USER="$(ls -ld $0 | awk '{print $3}')"

sed -e "s:/path/to/your/mapground/:${DIR}/:g" mapground-supervisor.conf > /etc/supervisor/conf.d/mapground-supervisor.conf
sed -i "s:mapground-user:${DEV_USER}:g" /etc/supervisor/conf.d/mapground-supervisor.conf

service supervisor restart