typedef struct {
    int size;
    char *data;
} DataBuffer;

void DataBufferInit(DataBuffer *self, int size);
void DataBufferUpdate(DataBuffer *self);

// methods to fit the data here

