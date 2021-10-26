#!/usr/bin/env bash

docker build -t tests --add-host app.ecwid.com:127.0.0.1 .

docker run --rm --add-host app.ecwid.com:127.0.0.1 tests
