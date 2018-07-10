#!/usr/bin/env bash
DIR="$( cd "$(dirname "$0")" ; pwd -P )"
cd ${DIR}
${DIR}/venv/bin/python manage.py process_tasks