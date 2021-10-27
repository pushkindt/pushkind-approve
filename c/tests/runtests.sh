#!/usr/bin/env sh

echo "Starting fake ecwid server:"

tests/ecwid/venv/bin/python3 tests/ecwid/app.py &
FLASK_PID=$!
sleep 5

echo "Running unit tests:"

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
            exit 1
        fi
    fi
done

kill $FLASK_PID

echo ""