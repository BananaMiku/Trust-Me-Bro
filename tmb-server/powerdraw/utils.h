#ifndef POWERDRAW_UTILS_H
#define POWERDRAW_UTILS_H

#include "./../stats_verify.h"
#include "./../utils.h"
#include <stdbool.h>

/*
Using MOM for t, alpha, and beta 
*/
betaParams betaDistroPower(DataBuffer *self);

/*
Helper method for the probability density function of a beta(0, 1) distribution
Returns probability of seeing the given data point on a cut off threshold
*/
double betaLogPDF_Power(double data, double alpha, double beta);

/*
PDF inference on incoming data
*/
bool betaDistroPowerInference(double data, betaParams params);

#endif