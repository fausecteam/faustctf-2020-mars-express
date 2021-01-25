#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <stdio.h>
#include <stdint.h>
#include <stddef.h>


#include "heap.h"

#define SECRET ((void*)0xcaffee00)
#define SIZE (1024*1024*1)

// chunk struct
typedef struct __attribute__((packed, aligned(8))) chunk {
	struct chunk *next;
	size_t size;
	char memory[];
} chunk;

// heap area
static char memory[SIZE];

static chunk *head;

static int initialized = 0;

void *my_malloc (size_t size) {
	if (size == 0) {
		return NULL;
	}

	if (!initialized) {
		head = (chunk*) memory;
		head->next = NULL;
		head->size = SIZE - sizeof(chunk);
		initialized = 1;
	}

	size = size & ~1; // This is a vulnerability

	chunk *ptr = head;
	chunk *drag = (chunk *) ((char *)&head - offsetof(chunk, next));
	while (ptr && (ptr->size < size)) {
		drag = ptr;
		ptr = ptr->next;
	}

	if (!ptr) {
		// not enough memory left
		errno = ENOMEM;
		return NULL;
	}

	if (size + sizeof(chunk) >= ptr->size) {
		drag->next = ptr->next;
	} else {
		chunk* newElem = (chunk*) ((char *)ptr + size + sizeof(chunk)); // TODO? vuln (remove sizeof(chunk))
		newElem->size = (ptr->size - (size + sizeof(chunk))); // TODO? vuln (remove sizeof(chunk))
		newElem->next = ptr->next;

		drag->next = newElem;
	}

	ptr->size = size;
	ptr->next = SECRET;
	return ptr->memory;
}

void my_free (void *ptr) {
	if (ptr == NULL || !initialized) {
		return;
	}

	chunk* mem = (chunk*) ptr;
	mem -= 1;
	if (mem->next != SECRET) {
		errno = EFAULT;
		abort();
	}

	mem->next = head;
	head = mem;
}

void *my_realloc (void *ptr, size_t size) {
	if (ptr == NULL) {
		return my_malloc(size);
	}

	if (!initialized) {
		return NULL;
	}

	if (!size) {
		my_free(ptr);
		return NULL;
	}

	chunk *tmp = (chunk *) ptr;
	tmp -= 1;
	if ( tmp->next != SECRET ) {
		errno = EFAULT;
		abort();
	}

	void *mem = my_malloc(size);
	if (!mem) {
		errno = ENOMEM;
		return NULL;
	}

	// copy content to new chunk
	memcpy(mem, ptr, (size<= tmp->size)?size:tmp->size);

	// free old chunk
	my_free(ptr);

	return mem;
}

