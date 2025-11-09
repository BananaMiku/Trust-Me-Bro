#ifndef STATS_VERIFY_H
#define STATS_VERIFY_H

// for each row of the csv file
typedef struct {
    double gpuUtilization;
    double vramUsage;
    double powerDraw;
} DataRow;

// contains the entire CSV
typedef struct {
    int totalCapacity;
    int currCapacity;
    DataRow *row;
} DataBuffer;


void DataBufferInit(DataBuffer *self, int totalCapacity);
void DataBufferRead(DataBuffer *self, const char *filePath);
void DataBufferPrint(const DataBuffer *self);

#endif