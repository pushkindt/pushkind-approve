.PHONY: ecwid run

ecwid:
	c/tests/ecwid/venv/bin/python3 c/tests/ecwid/app.py &

run:
	bash -c 'source venv/bin/activate && flask run'

icu:
	gcc -shared icu.c -g -o libsqliteicu.so -fPIC `pkg-config --libs --cflags icu-uc icu-io`
