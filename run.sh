#!/bin/bash
export DJANGO_SETTINGS_MODULE="config.settings.production"
SCRIPT_PATH=$(dirname $(realpath $0))
LOGS_PATH=$SCRIPT_PATH"/logs"
TMP_PATH=$SCRIPT_PATH"/tmp"

if [ ! -d $LOGS_PATH ] ; then
  mkdir -p $LOGS_PATH
fi

if [ ! -d $TMP_PATH ] ; then
  mkdir -p $TMP_PATH
fi

source $SCRIPT_PATH/venv/bin/activate
$SCRIPT_PATH/venv/bin/python3 $SCRIPT_PATH/manage.py crontab add

sleep 3

nohup uwsgi --ini $SCRIPT_PATH/config/uwsgi.ini >/dev/null 2>&1 &
deactivate
