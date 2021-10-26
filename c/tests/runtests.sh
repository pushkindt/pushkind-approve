#!/usr/bin/env bash

echo "Starting test docker container:"

container_id=`docker run --rm -d -p 127.0.0.1:8080:80/tcp kennethreitz/httpbin`

sleep 5

echo "Container ID is $container_id"

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

echo "Stopping test docker container:"

docker stop $container_id

echo ""