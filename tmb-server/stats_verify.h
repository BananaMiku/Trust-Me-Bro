// for each row of the csv file
typedef struct {
    float gpuUtilization;
    float vramUsage;
    float powerDraw;
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

// methods to fit the data here

