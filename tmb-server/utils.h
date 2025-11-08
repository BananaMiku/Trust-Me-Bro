/*
Struct to keep relevant information
*/
typedef struct {
    float gpuSampleMean;
    float vramSampleMean;
    float powerDrawSampleMean;
    float gpuSampleVariance;
    float vramSampleVariance;
    float powerDrawSampleVariance;
} Stats;

typedef struct {
    double alpha;
    double beta;
} betaParams;

/*
Calculates sample mean of the data
*/
Stats sampleMean(DataBuffer *self) {}
/*
Calculates the sample variance of the data
*/
Stats sampleVariance(DataBuffer *self) {}

/*
Using MOM for t, alpha, and beta 
*/
betaParams betaDistroGPU(DataBuffer *self) {}

/*
PDF inference on incoming data
*/
bool betaDistroGPUInference(float data, betaParams params) {}

/*
Helper method for the probability density function of a beta(0, 1) distribution
Returns probability of seeing the given data point on a cut off threshold
*/
float betaLogPDF(float data, betaParams params) {}

void betaDistroVRAM() {}
void gammaDistroPower(){}