
#ifndef UTIL_H
#define UTIL_H

#define LOCO_LENGTH 39
#define WAGON_LENGTH 46
#define TRAIN_HEIGHT 5

char *get_string_malloc();
int get_string(char *buf, int size);
char get_char();

void wait_graceful_shutdown();
void graceful_shutdown();

char get_loco_char(size_t x, size_t y);
char get_wagon_char(size_t x, size_t y, char *name, char c);

#endif
