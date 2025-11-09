#include "utils.h"
#include <float.h>
#include <stdio.h>
#include <math.h>
#include <gsl/gsl_sf_psi.h>
#include <gsl/gsl_sf_gamma.h>
#define EPSILON DBL_EPSILON
// if you have mac, compile:
// gcc utils.c -I/opt/homebrew/include -L/opt/homebrew/lib -lgsl -lgslcblas -lm

betaParams betaDistroVRAM(DataBuffer *self) {
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
    stats = sampleVariance(self, stats);

    // Method of Moments initialization for t, alpha, and beta
    double mean = stats.gpuSampleMean;
    double variance = stats.gpuSampleVariance;
    double alpha, beta;
    // add numerical guard
    if (variance <= 0.0) {
        // default
        alpha = 1.0, beta = 1.0;
    } else {
        double t = (mean * (1 - mean)) / (variance) - 1;
        alpha = fmax(EPSILON, stats.gpuSampleMean * t);
        beta = fmax(EPSILON, (1 - stats.gpuSampleMean) * t);
    }


    // summing logs for scoring function
    // log() is natural log
    double sumLogX = 0.0, sumLog1MinusX = 0.0;
    for (int i = 0; i < n; i++) {
        sumLogX += log(self->row[i].gpuUtilization);
        sumLog1MinusX += log(1.0 - self->row[i].gpuUtilization);
    }

    // Newton methods for optimization
    for (int iter = 0; iter < 50; ++iter) {
        double alphaBeta = alpha + beta;

        // gradients from score vectors
        double g1 = n * (gsl_sf_psi(alphaBeta) - gsl_sf_psi(alpha)) + sumLogX;
        double g2 = n * (gsl_sf_psi(alphaBeta) - gsl_sf_psi(beta))  + sumLog1MinusX;

        // Hessian entries from digamma derivatives
        double A = gsl_sf_psi_1(alphaBeta) - gsl_sf_psi_1(alpha);
        double B = gsl_sf_psi_1(alphaBeta) - gsl_sf_psi_1(beta);
        double C = gsl_sf_psi_1(alphaBeta);
        // fabs() -> doubleing absolute value
        double D = A * B - C * C;
        if (fabs(D) < 1e-14) {
            break;
        }

        double dalpha = ( B * g1 - C * g2) / D;
        double dbeta  = (-C * g1 + A * g2) / D;

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

double betaLogPDF_VRAM(double data, double alpha, double beta) {
    double lnB = gsl_sf_lngamma(alpha) + gsl_sf_lngamma(beta) - gsl_sf_lngamma(alpha + beta);
    return (alpha - 1) * log(data) + (beta - 1)  * log(1.0 - data) - lnB;
}

bool betaDistroVRAMInference(double data, betaParams params) {
    // hard coded cut off threshold
    return betaLogPDF_VRAM(data, params.alpha, params.beta) > log(0.1f) ? true : false;
}