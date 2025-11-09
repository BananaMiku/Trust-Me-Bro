#include "utils.h"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

// typedef struct {
//     double mean1;
//     double std1;
//     double mean2;
//     double std2;
//     double weight1;
//     double weight2;
// } BimodalParams;

// helper: Gaussian PDF
static double gaussianPDF(double x, double mean, double std) {
    double coeff = 1.0 / (std * sqrt(2 * M_PI));
    double expPart = exp(-0.5 * pow((x - mean)/std, 2));
    return coeff * expPart;
}

// comparison function for qsort
int cmpfunc(const double *a, const double *b) { 
    return (*a > *b) - (*a < *b); 
}

// estimate bimodal parameters (simple EM-like)
BimodalParams bimodalFitPower(DataBuffer *self) {
    int n = self->currCapacity;
    if (n < 2) {
        BimodalParams invalid = { NAN, NAN, NAN, NAN, NAN, NAN };
        perror("Insufficient data for bimodal fit!");
        return invalid;
    }

    // simple initialization: split at median
    double *data = malloc(sizeof(double) * n);
    for (int i = 0; i < n; i++)
        data[i] = self->row[i].powerDraw;

    // compute median
    double median;
    qsort(data, n, sizeof(double), (int(*)(const void*, const void*)) (cmpfunc));
    if (n % 2 == 0) median = (data[n/2 - 1] + data[n/2])/2.0;
    else median = data[n/2];

    // phase 1: <= median, phase 2: > median
    double sum1=0, sum2=0;
    int count1=0, count2=0;
    for (int i=0;i<n;i++) {
        if (data[i]<=median) { sum1+=data[i]; count1++; }
        else { sum2+=data[i]; count2++; }
    }
    double mean1 = sum1/count1;
    double mean2 = sum2/count2;

    // compute stds
    double sqsum1=0, sqsum2=0;
    for (int i=0;i<n;i++) {
        if (data[i]<=median) sqsum1 += pow(data[i]-mean1,2);
        else sqsum2 += pow(data[i]-mean2,2);
    }
    double std1 = sqrt(sqsum1/(count1-1));
    double std2 = sqrt(sqsum2/(count2-1));

    BimodalParams params = {
        mean1, std1, mean2, std2,
        (double)count1/n, (double)count2/n
    };

    //     // gradients from score vectors
    //     double g1 = n * (gsl_sf_psi(alphaBeta) - gsl_sf_psi(alpha)) + sumLogX;
    //     double g2 = n * (gsl_sf_psi(alphaBeta) - gsl_sf_psi(beta))  + sumLog1MinusX;

    //     // Hessian entries from digamma derivatives
    //     double A = gsl_sf_psi_1(alphaBeta) - gsl_sf_psi_1(alpha);
    //     double B = gsl_sf_psi_1(alphaBeta) - gsl_sf_psi_1(beta);
    //     double C = gsl_sf_psi_1(alphaBeta);
    //     // fabs() -> doubleing absolute value
    //     double D = A * B - C * C;
    //     if (fabs(D) < 1e-14) {
    //         break;
    //     }

    //     double dalpha = ( B * g1 - C * g2) / D;
    //     double dbeta  = (-C * g1 + A * g2) / D;

    //     // slows Newton methods to prevent divergence
    //     alpha -= 0.1 * dalpha;
    //     beta  -= 0.1 * dbeta;

    //     if (alpha <= 0) alpha = 1e-6;
    //     if (beta  <= 0) beta  = 1e-6;

    //     if (fabs(dalpha) < 1e-8 * fabs(alpha) && fabs(dbeta) < 1e-8 * fabs(beta)) {
    //         break;
    //     }
    // }

    // betaParams params = { alpha, beta };
    free(data);
    return params;
}

// inference
bool bimodalPowerInference(double x, BimodalParams params) {
    double p = params.weight1 * gaussianPDF(x, params.mean1, params.std1)
             + params.weight2 * gaussianPDF(x, params.mean2, params.std2);
    return p > 0.05; // threshold can be tuned
}