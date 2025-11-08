#include <stdio.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <float.h>
#include "utils.h"
#include "stats_verify.h"
#include <gsl/gsl_sf_psi.h>
#include <gsl/gsl_sf_gamma.h>
#define EPSILON DBL_EPSILON

Stats sampleMean(DataBuffer *self) {
    float gpuSum = 0.0, vramSum = 0.0, powerSum = 0.0;

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
    float gpuSampleMean = stats.gpuSampleMean;
    float vramSampleMean = stats.vramSampleMean;
    float powerDrawSampleMean = stats.powerDrawSampleMean;
    float gpuSum = 0.0, vramSum = 0.0, powerSum = 0.0;

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


betaParams betaDistroGPU(DataBuffer *self) {
    // numerical percision
    int n = self->currCapacity;
    // need many data points for the distro to work
    if (n < 2) {
        betaParams invalid = { NAN, NAN };
        perror("Insufficient Data Points!");
        return invalid;
    }

    // compute sample mean and variance
    Stats stats;
    stats = sampleMean(self);
    stats = sampleVariance(*self, stats);

    // Method of Moments initialization for t, alpha, and beta
    float mean = stats.gpuSampleMean;
    float variance = stats.gpuSampleVariance;
    float alpha, beta;
    // add numerical guard
    if (variance <= 0.0) {
        // default
        alpha = 1.0, beta = 1.0;
    } else {
        float t = (mean * (1 - mean)) / (variance) - 1;
        alpha = fmax(EPSILON, stats.gpuSampleMean * t);
        beta = fmax(EPSILON, (1 - stats.gpuSampleMean) * t);
    }


    // summing logs for scoring function
    // log() is natural log
    float sumLogX = 0.0, sumLog1MinusX = 0.0;
    for (int i = 0; i < n; i++) {
        sumLogX += log(self->row[i].gpuUtilization);
        sumLog1MinusX += log(1.0 - self->row[i].gpuUtilization);
    }

    // Newton methods for optimization
    for (int iter = 0; iter < 50; ++iter) {
        float alphaBeta = alpha + beta;

        // gradients from score vectors
        float g1 = n * (gsl_sf_psi(alphaBeta) - gsl_sf_psi(alpha)) + sumLogX;
        float g2 = n * (gsl_sf_psi(alphaBeta) - gsl_sf_psi(beta))  + sumLog1MinusX;

        // Hessian entries from digamma derivatives
        float A = gsl_sf_psi_1(alphaBeta) - gsl_sf_psi_1(alpha);
        float B = gsl_sf_psi_1(alphaBeta) - gsl_sf_psi_1(beta);
        float C = gsl_sf_psi_1(alphaBeta);
        // fabs() -> floating absolute value
        float D = A * B - C * C;
        if (fabs(D) < 1e-14) {
            break;
        }

        float dalpha = ( B * g1 - C * g2) / D;
        float dbeta  = (-C * g1 + A * g2) / D;

        alpha -= dalpha;
        beta  -= dbeta;

        if (alpha <= 0) alpha = 1e-6;
        if (beta  <= 0) beta  = 1e-6;

        if (fabs(dalpha) < 1e-8 * fabs(alpha) && fabs(dbeta) < 1e-8 * fabs(beta)) {
            break;
        }
    }

    betaParams params = { alpha, beta };
    return params;
}   

float betaLogPDF(float data, float alpha, float beta) {
    float lnB = gsl_sf_lngamma(alpha) + gsl_sf_lngamma(beta) - gsl_sf_lngamma(alpha + beta);
    return (alpha - 1) * log(data) + (beta - 1)  * log(1.0 - data) - lnB;
}

bool betaDistroGPUInference(float data, betaParams params, float threshold) {
    // hard coded cut off threshold
    return betaLogPDF(data, params.alpha, params.beta) > log(0.1f) ? true : false;
}