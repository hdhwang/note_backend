#!/bin/bash
export DJANGO_SETTINGS_MODULE="config.settings.production"
SCRIPT_PATH=$(dirname $(realpath $0))

RUN_PATH=${SCRIPT_PATH}/run
PID_FILE=${RUN_PATH}/note_drf.pid

source $SCRIPT_PATH/venv/bin/activate
if [ -f $PID_FILE ]; then
    # PID 파일이 있으면 종료
    kill -9 $(cat $PID_FILE)
    rm -f ${PID_FILE}
    echo "note_drf stopped successfully."
fi
deactivate
