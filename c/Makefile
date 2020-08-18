TARGET = ecwid-api
PREFIX ?= 
SRCS = ecwid-api.c model.c http.c rest.c ecwid.c
OBJS = $(SRCS:.c=.o)
CFLAGS_LOCAL =  -g -O0 -Wall -Wextra -include allheaders.h `curl-config --cflags` $(shell pkg-config --cflags json-c)
LDFLAGS_LOCAL = -g -O0 -lsqlite3 `curl-config --libs` -lm $(shell pkg-config --libs json-c)
CC = clang

.PHONY: all clean

all: $(TARGET)
$(TARGET): $(OBJS)
	$(CC)  $(OBJS) $(LDFLAGS_LOCAL) -o $(TARGET)
	
%.o: %.c
	$(CC) -c $(CFLAGS_LOCAL) $< -o $@

clean:
	rm -rf $(TARGET) $(OBJS)