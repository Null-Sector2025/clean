CC = aarch64-linux-android24-clang
TARGET = libstrong_core.so
SRC = strong_core.c
CFLAGS = -shared -fPIC -s -ldl -Wall

all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) $^ -o $@

clean:
	rm -f $(TARGET)
