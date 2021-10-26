icu:
	gcc -shared icu.c -g -o libsqliteicu.so -fPIC `pkg-config --libs --cflags icu-uc icu-io`
