#ifndef SERVER_H_
#define SERVER_H_
#include "globals.h"

void serve(int port, struct Model* models);

typedef struct {
    char* original; 
    char uuid[36];
    char* model;
} InternalRequest;

InternalRequest* parse_internal_request(const char* json_str);

void free_internal_request(InternalRequest* req);
#endif
