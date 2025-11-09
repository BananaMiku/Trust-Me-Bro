#include "utils.h"
#include <float.h>
#include <stdio.h>
#include <math.h>
#include <gsl/gsl_sf_psi.h>
#include <gsl/gsl_sf_gamma.h>
#define EPSILON DBL_EPSILON
#define LOWER_BOUND 1e-14
#define SMALL_ALPHA 1e-6
#define SMALL_BETA 1e-6
#define SMALL_DELTA 1e-8
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
    double mean = stats.vramSampleMean;
    double variance = stats.vramSampleVariance;
    double alpha, beta;
    // add numerical guard
    if (variance <= 0.0) {
        // default
        alpha = 1.0, beta = 1.0;
    } else {
        double t = (mean * (1 - mean)) / (variance) - 1;
        alpha = fmax(EPSILON, stats.vramSampleMean * t);
        beta = fmax(EPSILON, (1 - stats.vramSampleMean) * t);
    }


    // summing logs for scoring function
    // log() is natural log
    double sumLogX = 0.0, sumLog1MinusX = 0.0;
    for (int i = 0; i < n; i++) {
        sumLogX += log(self->row[i].vramUsage);
        sumLog1MinusX += log(1.0 - self->row[i].vramUsage);
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
        if (fabs(D) < LOWER_BOUND) {
            break;
        }

        double dalpha = ( B * g1 - C * g2) / D;
        double dbeta  = (-C * g1 + A * g2) / D;

        // slows Newton methods to prevent divergence
        alpha -= 0.1 * dalpha;
        beta  -= 0.1 * dbeta;

        if (alpha <= 0) alpha = SMALL_ALPHA;
        if (beta  <= 0) beta  = SMALL_BETA;

        if (fabs(dalpha) < SMALL_DELTA * fabs(alpha) && fabs(dbeta) < SMALL_DELTA * fabs(beta)) {
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
    return betaLogPDF_VRAM(data, params.alpha, params.beta) > 0.1 ? true : false;
}