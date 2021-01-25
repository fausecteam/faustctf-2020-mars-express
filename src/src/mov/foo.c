#include <stdio.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <string.h>


int fd;
int seed;


int save_init(int new_seed, char *fname) {
	fd = open(fname, O_WRONLY|O_EXCL|O_CREAT, S_IRUSR|S_IWUSR);
	if (fd < 0) {
		return -1;
	}

	seed = new_seed;

	if (-1 == write(fd, &seed, 4)) {
		return -1;
	}

	return 0;
}

int save_write_wagon(char *content) {
	char buf[100];
	int i, length;

	length = strlen(content);

	buf[0] = (char) length+1;
	strcpy(&buf[1], content);

	for (i = 0; i<(length/4)+1; i++) {
		((int*)&buf)[i] = ((int*)&buf)[i] ^ seed;
	}

	if (-1 == write(fd, buf, length+2)) {
		return -1;
	}
	return 0;
}

int save_finish() {
	int ret;
	ret = close(fd);
	fd = 0;
	return ret;
}

int load_init(char *fname) {
	fd = open(fname, O_RDONLY);
	if (fd < 0) {
		return -1;
	}

	if (4 != read(fd, &seed, 4)) {
		return -1;
	}

	return 0;
}

char buf[256];

char *load_read_wagon() {
	unsigned int i, length;

	length = 0;

	if (1 != read(fd, &length, 1)) {
		return NULL;
	}

	length ^= (unsigned char) seed;

	if ((int)length != read(fd, &buf[1], length)) {
		return NULL;
	}

	for (i = 0; i<(length/4)+1; i++) {
		((int*)&buf)[i] = ((int*)&buf)[i] ^ seed;
	}

	buf[length] = '\0';

	return &buf[1];
}
