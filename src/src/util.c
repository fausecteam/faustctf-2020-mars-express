#include <stdlib.h>
#include <string.h>
#include <ncurses.h>

#include "util.h"
#include "heap.h"

static char *loco[5] = {
 "         _____________________________ ",
 "    _,-'/| #### | |          ####     |",
 " _-'            | |                   |",
 "(------------------mars-express-------|",
" \\----(o)~~~~(o)----------(o)~~~~(o)--'",
};



char *get_string_malloc() {
	char *ret;
	char buf[100];

	int size = get_string(buf, sizeof(buf));

	ret = my_malloc(size+1);
	if (!ret) {
		fprintf(stderr, "malloc failed\n");
		graceful_shutdown();
	}

	memcpy(ret, buf, size+1);
	return ret;
}

int get_string(char *buf, int size) {
	if (size<4 || !buf) {
		graceful_shutdown();
	}
	//getnstr(buf, size-1);
	int i;

	for(i = 0; i<size; i++) {
		int c = getch();
		if(c == ERR || c == '\n') {
			//buf[i] = '\n';
			break;
		} else {
			buf[i] = (char) c;
		}
	}

	buf[i] = '\0';
	return i;
}

char get_char() {
	char buf[4];
	get_string(buf, sizeof(buf));
	return buf[0];
}



void wait_graceful_shutdown() {
	noecho();
	getch();
	endwin();
	exit(0);
}

void graceful_shutdown() {
	noecho();
	endwin();
	exit(0);
}



char get_loco_char(size_t y, size_t x) {
	if (y > TRAIN_HEIGHT) return ' ';
	if (x > LOCO_LENGTH) return ' ';

	return loco[y][x];
}

char get_wagon_char(size_t y, size_t x, char *name, char c) {
	if (y > TRAIN_HEIGHT) return ' ';
	if (x > WAGON_LENGTH) return ' ';

	int max_content_length = strlen(name) > WAGON_LENGTH-6 ? WAGON_LENGTH-6 : strlen(name);

	int before = (WAGON_LENGTH - 4 - max_content_length)/2;
	int after = WAGON_LENGTH - 4 - before - max_content_length;
	char buf[WAGON_LENGTH+1];
	buf[0] = '\0';

	switch (y) {
		case 0: 
			{
				sprintf(buf, " ");
				for (int i = 0; i<WAGON_LENGTH-2; i++) {
					strcat(buf, "_");
				}
				strcat(buf, " ");
				break;
			}
		case 1: 
			{
				strcat(buf, "|");
				for (int i = 0; i<WAGON_LENGTH-2; i++) {
					strncat(buf, &c, 1);
				}
				strcat(buf, "|");
				break;
			}
		case 2: 
			{
				strcat(buf, "|");

				for (int i = 0; i<before; i++) {
					strncat(buf, &c, 1);
				}

				strcat(buf, " ");
				strncat(buf, name, max_content_length);
				strcat(buf, " ");

				for (int i = 0; i<after; i++) {
					strncat(buf, &c, 1);
				}

				strcat(buf, "|");
				break;
			}
		case 3:
			{
				sprintf(buf, "|");
				for (int i = 0; i<WAGON_LENGTH-2; i++) {
					strcat(buf, "-");
				}
				strcat(buf, "|");
				break;
			}
		case 4:
			{
				sprintf(buf, "`-----(o)~~~~(o)");
				for (int i = 0; i<WAGON_LENGTH-32; i++) {
					strcat(buf, "-");
				}
				strcat(buf, "(o)~~~~(o)-----'");
				break;
			}
	}

	return buf[x];
}
