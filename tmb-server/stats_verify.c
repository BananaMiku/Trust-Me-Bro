#include <stdio.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include "stats_verify.h"
#include "utils.c"
#define MAX_BUFFER 256
#define SMI_DATA_LEN 3

// entry point
// simple local test:
// ./stats_verify GPT-5_storage.csv 22.2 42.24 57.321
int main(int argcnt, char *argls[]) {
    printf("C file!\n");
    fflush(stdout);
    // arcnt + length of argls
    assert(argcnt == 5);
    const char *filePath = argls[1];

    DataBuffer buffer;
    // TODO with python, move 10, the buffer size to a global config file
    DataBufferInit(&buffer, 10);
    DataBufferRead(&buffer, filePath);
    // DataBufferPrint(&buffer);
    betaParams params = betaDistroGPU(&buffer);
    float data = 0.5;
    foo = betaDistroGPUInference(data, params);
    printf("Checking bool bool: ");
    printf(boo);

    return 0;
}

/*
Initializes an empty reservoir for all data
Memory = reservoir size * DataRow size
*/
void DataBufferInit(DataBuffer *self, int totalCapacity) {
    self->totalCapacity = totalCapacity;
    self->currCapacity = 0;
    self->row = malloc(sizeof(DataRow) * self->totalCapacity);
    if (!self->row) {
        perror("Memory Allocation Failed");
        exit(1);
    }
}

/*
Read the reservoir via CSV file
Reservoir sampling
*/
void DataBufferRead(DataBuffer *self, const char * filePath) {
    FILE *file = fopen(filePath, "r");

    if (!file) {
        perror("Error Opening File:");
        exit(1);
    }

    char line[MAX_BUFFER];
    int lineNum = 0;

    while (fgets(line, sizeof(line), file)) {
        // check for overflow
        if (self->currCapacity >= self->totalCapacity) {
            perror("Buffer Overflow!");
            break;
        }

        // skip header
        if (lineNum++ == 0) continue;

        // remove trailing newline
        line[strcspn(line, "\n")] = 0;

        // parse by comma
        char *token = strtok(line, ",");
        if (!token) continue;  // skip potentially malformed line?

        DataRow row;
        row.gpuUtilization = strtof(token, NULL);

        token = strtok(NULL, ",");
        row.vramUsage = token ? strtof(token, NULL) : 0.3f;

        token = strtok(NULL, ",");
        row.powerDraw = token ? strtof(token, NULL) : 0.3f;

        self->row[self->currCapacity++] = row;
    }

    fclose(file);
}

/*
For testing purposes
*/
void DataBufferPrint(const DataBuffer *self) {
    printf("DataBuffer Content: \n");
    for (int i = 0; i < self->currCapacity; i++) {
        printf("Row %d", i);
        printf("GPU Utillization: %f\n", self->row[i].gpuUtilization);
        printf("VRAM Usage: %f\n", self->row[i].vramUsage);
        printf("Power Draw: %f\n", self->row[i].powerDraw);
    }
}
