#ifndef SERVER_H_
#define SERVER_H_

void serve(int port);

typedef struct {
    char uuid[36];
    char* prompt;
    char* model;

} PromptRequest;

typedef struct {
    PromptRequest original; 
    char uuid[36];
    char* model;
} InternalRequest;

typedef struct {
    char* model;
    int port;
} PortToModel;

PromptRequest* parse_prompt_request(const char* json_str);
InternalRequest* parse_internal_request(const char* json_str);
PortToModel* parse_port_to_model(const char* json_str);

void free_prompt_request(PromptRequest* req);
void free_internal_request(InternalRequest* req);
void free_port_to_model(PortToModel* req);
#endif
