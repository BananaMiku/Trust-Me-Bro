#ifndef UTILS_H
#define UTILS_H

#include "./stats_verify.h"
#include <stdbool.h>

/*
Struct to keep relevant information
*/
typedef struct {
    double gpuSampleMean;
    double vramSampleMean;
    double powerDrawSampleMean;
    double gpuSampleVariance;
    double vramSampleVariance;
    double powerDrawSampleVariance;
} Stats;

typedef struct {
    double alpha;
    double beta;
} betaParams;

/*
Calculates sample mean of the data
*/
Stats sampleMean(DataBuffer *self);

/*
Calculates the sample variance of the data
*/
Stats sampleVariance(DataBuffer *self, Stats stats);

/*
Using MOM for t, alpha, and beta 
*/
betaParams betaDistroGPU(DataBuffer *self);

/*
Helper method for the probability density function of a beta(0, 1) distribution
Returns probability of seeing the given data point on a cut off threshold
*/
double betaLogPDF(double data, double alpha, double beta);

/*
PDF inference on incoming data
*/
bool betaDistroGPUInference(double data, betaParams params);

// void betaDistroVRAM();
// void gammaDistroPower();

#endif