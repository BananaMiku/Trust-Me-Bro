#include "server.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <regex.h>

// Helper to extract a string value from JSON by key
static char* extract_json_string(const char* json, const char* key) {
    char* key_pos = strstr(json, key);
    if (!key_pos) return NULL;

    char* colon = strchr(key_pos, ':');
    if (!colon) return NULL;

    // Skip whitespace
    colon++;
    while (*colon == ' ' || *colon == '\"') colon++;

    char* end = colon;
    while (*end && *end != '\"' && *end != ',' && *end != '}') end++;

    size_t len = end - colon;
    char* value = malloc(len + 1);
    if (!value) return NULL;
    strncpy(value, colon, len);
    value[len] = '\0';
    return value;
}

// Parse InternalRequest
InternalRequest* parse_internal_request(const char* json_str) {

    InternalRequest req;

    regex_t uuid_rxp;
    regex_t model_rxp;
    regex_t original_rxp;
    regmatch_t grouparray[1];

    if (
        !regcomp(&uuid_rxp, "\"uuid\":[:space:]*\"(.*)\"", REG_EXTENDED)
        || !regcomp(&model_rxp, "\"model\":[:space:]*\"(.*)\"", REG_EXTENDED)
        || !regcomp(&original_rxp, "\"original\":[:space:]*\"(.*)\"", REG_EXTENDED)
    ) {
        perror("could not compile regex");
        exit(1);
    }

    if (regexec(&uuid_rxp, json_str, 1, grouparray, 0) != 0) {
        perror("failed to match for uuid");
        exit(1);
    }
    req.uuid = grouparray[0].rm_eo;
    if (regexec(&model_rxp, json_str, 1, grouparray, 0) != 0) {
        perror("failed to match for model");
        exit(1);
    }
    req.model = grouparray[0].rm_eo;
    if (regexec(&original_rxp, json_str, 1, grouparray, 0) != 0) {
        perror("failed to match for original");
        exit(1);
    }
    req.original = grouparray[0].rm_eo;
    
    return &req;
}


void free_internal_request(InternalRequest* req) {
    if (!req) return;
    free(req->original);
    free(req->model);
    free(req);
}
// Helper to extract an int value from JSON by key
static int extract_json_int(const char* json, const char* key) {
    char* key_pos = strstr(json, key);
    if (!key_pos) return 0;

    char* colon = strchr(key_pos, ':');
    if (!colon) return 0;

    colon++;
    while (*colon == ' ') colon++;

    int value = 0;
    sscanf(colon, "%d", &value);
    return value;
}

