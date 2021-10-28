#!/usr/bin/env sh
echo "Starting fake ecwid server:"

tests/ecwid/venv/bin/python3 tests/ecwid/app.py 2> /dev/null &
FLASK_PID=$!
export REST_URL=http://127.0.0.1:5000/api/v3
DATABASE_FILE=test.db
export DATABASE_URL=file:$DATABASE_FILE
sqlite3 $DATABASE_FILE < test.sql
sleep 5

echo "Running unit tests:"

GracefulShutdown() {
    kill $1
    unset REST_URL
    unset DATABASE_URL
}

for i in tests/*_tests
do
    if [ -f $i ]
    then
        if $VALGRIND ./$i 2>> tests/tests.log
        then
            echo $i PASS
        else
            echo "ERROR in test $i: here's tests/tests.log"
            echo "------"
            tail tests/tests.log
            GracefulShutdown $FLASK_PID
            exit 1
        fi
    fi
done

GracefulShutdown $FLASK_PID

echo ""