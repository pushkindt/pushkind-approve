TARGET = ecwid-api
PREFIX ?= 
SRCS = model.c http.c rest.c ecwid.products.c ecwid.orders.c ecwid.profiles.c ecwid.categories.c util.c ecwid-api.c
OBJS = $(SRCS:.c=.o)
CFLAGS_LOCAL =  -std=c17 -g -O0 -Wall -Wextra -Wshadow -Werror -include allheaders.h `curl-config --cflags` $(shell pkg-config --cflags json-c)
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