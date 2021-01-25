#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <errno.h>
#include <stdio.h>
#include <ncurses.h>
#include <time.h>

#include "util.h"
#include "train.h"
#include "heap.h"


extern int call(void (*)(void), int a, int b, int c);
void save_init();
void save_write_wagon();
void save_finish();
void load_init();
void load_read_wagon();



typedef struct __attribute__((aligned(8))) wagon {
	char *name;
	char c;
	struct wagon *next;
} wagon;

wagon *head = NULL;

static wagon *get_wagon_nr(size_t i) {
	wagon *ptr = head;
	while (ptr) {
		if (i == 0) {
			return ptr;
		}
		ptr = ptr->next;
		i--;
	}
	return NULL;
}

static size_t get_train_size() {
	size_t size = 0;
	wagon *ptr = head;
	while (ptr) {
		ptr = ptr->next;
		size++;
	}
	return size;
}



int save_train(char *name) {
	if (!head) {
		return 1;
	}

	char filename[sizeof(SAVE_DIR)+32+7];
	strcpy(filename, SAVE_DIR);
	// Here is a path traversal attack possible. This (hopefully) is not usable for anything.
	strcat(filename, name);
	strcat(filename, ".train");

	int seed = random();
	if (0 != call(save_init, seed, (int)filename, 0)) {
		return 2;
	}

	wagon *ptr = head;
	while (ptr) {
		char buf[strlen(ptr->name) + 2];
		sprintf(buf, "%c%s", ptr->c, ptr->name);

		if (0 != call(save_write_wagon, (int)buf, 0, 0)) {
			return 3;
		}

		ptr = ptr->next;
	}

	return 0;
}

int load_train(char *name) {
	char filename[sizeof(SAVE_DIR)+32+7];
	strcpy(filename, SAVE_DIR);
	strcat(filename, name);
	strcat(filename, ".train");

	if (0 != call(load_init, (int)filename, 0, 0)) {
		return -1;
	}

	while (true) {
		char *buf = (char *) call(load_read_wagon, 0, 0, 0);
		if (!buf) {
			break;
		}
		if (strlen(buf) < 2) {
			return -1;
		}

		char *dup = strdup(&buf[1]); // implicit malloc!
		if (!dup) {
			return -1;
		}

		if (0 != insert_wagon(dup, buf[0])) {
			break;
		}
	}

	return 0;
}



int insert_wagon(char *name, char c) {
	if (get_train_size() >= 15) {
		return -1;
	}

	if (strlen(name) > 40) {
		fprintf(stderr, "Name too long.\n");
		name[40] = '\0';
	}

	wagon *new = my_malloc(sizeof(wagon));
	if (!new) {
		fprintf(stderr, "malloc failed\n");
		graceful_shutdown();
	}
	new->name = name;
	new->c = c;
	new->next = NULL;

	if (head == NULL) {
		head = new;
		return 0;
	}

	wagon *ptr = head;
	while (ptr->next != NULL) {
		ptr = ptr->next;
	}
	ptr->next = new;
	return 0;
}

int remove_wagon(char *name) {
	if (!head) {
		return -1;
	}

	if (!strcmp(head->name, name)) {
		wagon *i = head;
		head = i->next;
		my_free(i->name);
		my_free(i);
		return 0;
	}

	wagon *ptr = head;
	while (ptr->next != NULL) {
		if (!strcmp(ptr->next->name, name)) {
			// remove the wagon
			wagon *i = ptr->next;
			ptr->next = i->next;

			my_free(i->name);
			my_free(i);
			return 0;
		}
		ptr = ptr->next;
	}
	return -1;
}



void print_train() {
	int overall_length = LOCO_LENGTH + (int) get_train_size()*WAGON_LENGTH + 1;

	int row, col;
	getmaxyx(stdscr, row, col);

	struct timespec tim, rem;
	tim.tv_sec  = 0;
	tim.tv_nsec = 50000000L;

	// prepare
	curs_set(0);
	clear();

	for (int offset = -col+4; offset < overall_length + 1; offset++) {
		clear();

		for (int i = 0; i<col; i++) {
			for (int j = 0; j<TRAIN_HEIGHT+1; j++) {

				if (i >= col-1) {
					// The last column only contains newlines
					mvaddch(j, i, '\n');
				} else if (j == TRAIN_HEIGHT) {
					// The last line only contains spaces
					mvaddch(j, i, ' ');
				} else if (offset+i<LOCO_LENGTH) {
					// this is the locomotive
					mvaddch(j, i, get_loco_char(j, offset+i));
				} else{
					// this is a wagon
					wagon *w = get_wagon_nr((offset+i-LOCO_LENGTH)/WAGON_LENGTH);
					if (w) {
						int w_i = (offset+i-LOCO_LENGTH)%WAGON_LENGTH;
						int w_j = j;

						mvaddch(j, i, get_wagon_char(w_j, w_i, w->name, w->c));
					} else {
						mvaddch(j, i, ' ');
					}
				}

			}
		}

		refresh();
		nanosleep(&tim, &rem);
	}
	curs_set(1);
}
