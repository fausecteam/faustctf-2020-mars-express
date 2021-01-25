
#ifndef TRAIN_H
#define TRAIN_H

#define SAVE_DIR "./data/"

int save_train(char *name);
int load_train(char *name);
int insert_wagon(char *name, char c);
int remove_wagon(char *name);
void print_train();

#endif
