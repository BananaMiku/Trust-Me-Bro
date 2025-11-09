#ifndef POWERDRAW_UTILS_H
#define POWERDRAW_UTILS_H

#include "./../stats_verify.h"
#include <stdbool.h>

/*
Struct to store parameters for a two-phase bimodal Gaussian model
*/
typedef struct {
    double mean1;   // mean of phase 1
    double std1;    // standard deviation of phase 1
    double mean2;   // mean of phase 2
    double std2;    // standard deviation of phase 2
    double weight1; // weight of phase 1 (fraction of points)
    double weight2; // weight of phase 2 (fraction of points)
} BimodalParams;

/*
Fit a bimodal Gaussian model to power draw data
Returns the estimated parameters
*/
BimodalParams bimodalFitPower(DataBuffer *self);

/*
Perform inference: check if a given power draw value is likely
according to the fitted bimodal Gaussian model
*/
bool bimodalPowerInference(double x, BimodalParams params);

#endif
