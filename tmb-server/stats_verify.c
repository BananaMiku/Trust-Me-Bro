#include <stdio.h>
#include <stdbool.h>
#include <stdlib.h>
#include <assert.h>
#include "stats_verify.h"

// entry point
int main(int argcnt, char *argls[]) {
    printf("C file!");
    // arcnt + length of argls
    assert(argcnt == 2);

    DataBuffer buffer;
    DataBufferInit(&buffer, 256);

    return 0;
}

/*
Initializes the reservoir for sampling of incoming data later
*/
void DataBufferInit(DataBuffer *self, int size) {
    self->size = size;
    self->data = malloc(size);
}

/*
Updates the reservoir with new data
Reservoir sampling
*/
void DataBufferUpdate(DataBuffer *self) {

}
