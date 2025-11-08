#ifndef SERVER_H_
#define SERVER_H_

void serve(int port);

typedef struct {
    char* original; 
    char uuid[36];
    char* model;
} InternalRequest;

InternalRequest* parse_internal_request(const char* json_str);

void free_internal_request(InternalRequest* req);
#endif
