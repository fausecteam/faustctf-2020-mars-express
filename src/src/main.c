#include <string.h>
#include <unistd.h>
#include <ncurses.h>

#include "util.h"
#include "train.h"



static char train_name[64];

static char *message = NULL;



static void menu() {
	clear();

	printw("Current train: %s\n\n", train_name);
	printw("What do you want to do?\n\n");
	printw("1: Append new wagon\n");
	printw("2: Unqueue a wagon\n");
	printw("3: Show current train\n");
	printw("4: Send the train!\n");
	printw("> ");

	if (message) {
		printw("\n\n%s\n", message);
	} else {
		printw("\n\n                    \n");
	}

	move(8, 2);
	refresh();

	message = NULL;
}

void ins() {
	printw("Give me the name: ");

	char *name = get_string_malloc();

	printw("And its symbol: ");
	char c = get_char();

	if (c<0x20 || c>0x7e) {
		c = ' ';
	}

	if (-1 == insert_wagon(name, c)) {
		message = "Train is too long. Dequeue some wagons before appending new.";
	} else {
		message = "Wagon inserted!";
	}
}

void rm() {
	printw("Give me the name of the wagon: ");
	char name[500];
	get_string(name, sizeof(name));

	if (0 != remove_wagon(name)) {
		message = "Did not find wagon!";
	} else {
		message = "Unqueued wagon!";
	}
}

void show_current() {
	print_train();
}

void send_train(char *name) {
	int ret = save_train(name);
	if (ret != 0) {
		printw("Sending failed.");
		wait_graceful_shutdown();
	}
	print_train();
	graceful_shutdown();
}


static void create_new() {
	printw("Give it a name: ");
	get_string(train_name, sizeof(train_name));

	if (strlen(train_name) < 8) {
		printw("Your train deserves a longer name!");
		wait_graceful_shutdown();
	}

	while (1) {
		menu();
		char c = get_char();
		//printw("%c\n", c);
		refresh();
		switch (c) {
			case '1': ins(); break;
			case '2': rm(); break;
			case '3': show_current(); break;
			case '4': send_train(train_name); break;
			default:
				printw("bad input");
				wait_graceful_shutdown();
		}
	}
}

static void print_previous() {
	printw("Give me the name of the train: ");
	char name[500];
	get_string(name, sizeof(name));
	int ret = load_train(name);
	if (ret != 0) {
		printw("Loading failed.");
		wait_graceful_shutdown();
	}
	print_train();
	graceful_shutdown();
}



int main(void) {
	setvbuf(stdin, NULL, _IONBF, 0);
	setvbuf(stdout, NULL, _IONBF, 0);

	alarm(120);

	// Start ncurses
	initscr();
	noecho();
	meta(stdscr, TRUE); // This forces ncurses to treat bytes as 8-bit values

	printw("Welcome to mars-express!\n");
	printw("Your friends need some tools at the\n");
	printw("outpost? Just send them a train - We\n");
	printw("deliver everything.\n\n");
	printw("Do you want to send a new train or\nshow a previous?\n\n");
	printw("1: Create and send new train\n");
	printw("2: Show a previous train\n");
	printw("> ");

	char c = get_char();
	refresh();
	switch (c) {
		case '1': create_new(); break;
		case '2': print_previous(); break;
		default: fprintf(stderr, "bad input\n"); wait_graceful_shutdown();
	}

	return 0;
}
