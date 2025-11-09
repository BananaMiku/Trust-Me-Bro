#include "utils.h"
#include <float.h>
#include <stdio.h>
#include <math.h>
#include <gsl/gsl_sf_psi.h>
#include <gsl/gsl_sf_gamma.h>
#define EPSILON DBL_EPSILON
// if you have mac, compile:
// gcc utils.c -I/opt/homebrew/include -L/opt/homebrew/lib -lgsl -lgslcblas -lm

Stats sampleMean(DataBuffer *self) {
    double gpuSum = 0.0, vramSum = 0.0, powerSum = 0.0;

    for (int i = 0; i < self->currCapacity; i++) {
        gpuSum += self->row[i].gpuUtilization;
        vramSum += self->row[i].vramUsage;
        powerSum += self->row[i].powerDraw;
    }

    int n = self->currCapacity;
    Stats aggregation = {gpuSum/n, vramSum/n, powerSum/n};
    return aggregation;
}


Stats sampleVariance(DataBuffer *self, Stats stats) {
    double gpuSampleMean = stats.gpuSampleMean;
    double vramSampleMean = stats.vramSampleMean;
    double powerDrawSampleMean = stats.powerDrawSampleMean;
    double gpuSum = 0.0, vramSum = 0.0, powerSum = 0.0;

    for (int i = 0; i < self->currCapacity; i++) {
        gpuSum += pow((self->row[i].gpuUtilization - gpuSampleMean), 2);
        vramSum += pow((self->row[i].vramUsage - vramSampleMean), 2);
        powerSum += pow((self->row[i].powerDraw - powerDrawSampleMean), 2);
    }
    int n = self->currCapacity - 1;
    stats.gpuSampleVariance = gpuSum / n;
    stats.vramSampleVariance = vramSum / n;
    stats.powerDrawSampleVariance = powerSum / n;
    return stats;
}