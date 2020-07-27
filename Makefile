icu:
	gcc -shared icu.c -g -o libsqliteicu.so -fPIC `icu-config --cppflags --ldflags`
