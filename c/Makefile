PREFIX ?= 
BUILD_DIR = build
SRC_DIR = src
TARGET = $(BUILD_DIR)/ecwid-api
SRCS = $(wildcard $(SRC_DIR)/**/*.c $(SRC_DIR)/*.c)
OBJS = $(subst $(SRC_DIR)/, $(BUILD_DIR)/, $(SRCS:.c=.o))
TEST_SRCS = $(wildcard tests/*_tests.c)
TEST_OBJS = $(filter-out $(addsuffix .o, $(TARGET)), $(OBJS))
TESTS = $(patsubst %.c,%,$(TEST_SRCS))
CFLAGS_PROD = -std=c17 -g -O0 -Wall -Wextra -Wshadow -Isrc -include allheaders.h `curl-config --cflags` $(shell pkg-config --cflags json-c) $(OPTGLAGS)
CFLAGS_DEV = -std=c17 -Isrc `curl-config --cflags` $(shell pkg-config --cflags json-c) $(OPTGLAGS) -D_DEFAULT_SOURCE
LDFLAGS = -g -O0 -lsqlite3 `curl-config --libs` -lm $(shell pkg-config --libs json-c)

.PHONY: dev all clean tests

all: $(TARGET) tests
dev: CFLAGS = $(CFLAGS_DEV)
dev: all
$(TARGET): build $(OBJS)
	$(CC) $(OBJS) $(LDFLAGS) -o $(TARGET)
	
tests: CFLAGS = $(CFLAGS_DEV) $(TEST_OBJS)
tests: build $(TEST_OBJS) $(TESTS) 
	sh ./tests/runtests.sh

$(BUILD_DIR)/%.o: $(SRC_DIR)/%.c
	$(CC) -c $(CFLAGS_PROD) $< -o $@

build:
	@mkdir -p build
	@mkdir -p bin
clean:
	rm -rf build $(TARGET)
	rm -f tests/tests.log
	rm -f $(TESTS)
	rm -f $(TEST_OBJS)
