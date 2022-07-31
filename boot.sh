#!/bin/bash
NUM_WORKERS=3
TIMEOUT=120

source venv/bin/activate
exec gunicorn -b :5000 --access-logfile - --workers $NUM_WORKERS --timeout $TIMEOUT -k gevent --error-logfile - approve:application
