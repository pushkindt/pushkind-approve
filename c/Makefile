PREFIX ?= 
BUILD_DIR = build
SRC_DIR = src
BIN_DIR = bin
TARGET = $(BUILD_DIR)/ecwid-api
SRCS = $(wildcard $(SRC_DIR)/**/*.c $(SRC_DIR)/*.c)
OBJS = $(subst $(SRC_DIR)/, $(BUILD_DIR)/, $(SRCS:.c=.o))
TEST_SRCS = $(wildcard tests/*_tests.c)
TEST_OBJS = $(filter-out $(addsuffix .o, $(TARGET)), $(OBJS))
TESTS = $(patsubst %.c,%,$(TEST_SRCS))
CFLAGS_PROD = -std=c17 -O3 -Isrc -Idotenv-c/src `curl-config --cflags` $(shell pkg-config --cflags json-c) $(OPTGLAGS) -D_DEFAULT_SOURCE -DNDEBUG
CFLAGS_DEV = -std=c17 -g -O0 -Isrc -Idotenv-c/src `curl-config --cflags` $(shell pkg-config --cflags json-c) $(OPTGLAGS) -D_DEFAULT_SOURCE
LDFLAGS = -lsqlite3 `curl-config --libs` -lm $(shell pkg-config --libs json-c)

.PHONY: dev all clean tests

all: CFLAGS = $(CFLAGS_PROD)
all: $(TARGET)
dev: CFLAGS = $(CFLAGS_DEV) -Wall -Wextra -Wshadow
dev: $(TARGET)
$(TARGET): LDFLAGS += $(BUILD_DIR)/libdotenv-s.a
$(TARGET): $(BUILD_DIR) $(OBJS)
	cp dotenv-c/build/lib* $(BUILD_DIR)
	$(CC) $(OBJS) $(LDFLAGS) -o $(TARGET)
	mv $(TARGET) $(BIN_DIR)
	
tests: CFLAGS = $(CFLAGS_DEV)
tests: $(BUILD_DIR) $(TEST_OBJS) $(TESTS)
	sh ./tests/runtests.sh

$(TESTS): CFLAGS += $(TEST_OBJS)

$(BUILD_DIR)/%.o: $(SRC_DIR)/%.c
	$(CC) -c $(CFLAGS) $< -o $@

build:
	@mkdir -p build
	@mkdir -p bin
clean:
	rm -rf $(BIN_DIR)/*
	rm -rf $(BUILD_DIR)
	rm -f tests/tests.log
	rm -f $(TESTS)
	rm -f $(TEST_OBJS)
	rm -rf test.db
