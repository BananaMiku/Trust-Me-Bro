#include "server.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

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

// Parse PromptRequest
PromptRequest* parse_prompt_request(const char* json_str) {
    if (!json_str) return NULL;

    PromptRequest* req = malloc(sizeof(PromptRequest));
    if (!req) return NULL;

    char* uuid = extract_json_string(json_str, "\"uuid\"");
    char* prompt = extract_json_string(json_str, "\"prompt\"");
    char* model = extract_json_string(json_str, "\"model\"");

    if (uuid) {
        strncpy(req->uuid, uuid, sizeof(req->uuid));
        free(uuid);
    } else {
        req->uuid[0] = '\0';
    }

    req->prompt = prompt;
    req->model = model;

    return req;
}

// Parse InternalRequest
InternalRequest* parse_internal_request(const char* json_str) {
    if (!json_str) return NULL;

    InternalRequest* req = malloc(sizeof(InternalRequest));
    if (!req) return NULL;

    // Extract "original" object
    char* original_start = strstr(json_str, "\"original\"");
    if (original_start) {
        char* brace_start = strchr(original_start, '{');
        char* brace_end = strchr(brace_start, '}');
        size_t len = brace_end - brace_start + 1;
        char* original_json = malloc(len + 1);
        strncpy(original_json, brace_start, len);
        original_json[len] = '\0';

        PromptRequest* original = parse_prompt_request(original_json);
        if (original) {
            req->original = *original;
            free(original);
        }
        free(original_json);
    } else {
        req->original.uuid[0] = '\0';
        req->original.prompt = NULL;
        req->original.model = NULL;
    }

    // Parse top-level uuid and model
    char* uuid = extract_json_string(json_str, "\"uuid\"");
    char* model = extract_json_string(json_str, "\"model\"");

    if (uuid) {
        strncpy(req->uuid, uuid, sizeof(req->uuid));
        free(uuid);
    } else {
        req->uuid[0] = '\0';
    }

    req->model = model;

    return req;
}

// Free functions
void free_prompt_request(PromptRequest* req) {
    if (!req) return;
    free(req->prompt);
    free(req->model);
    free(req);
}

void free_internal_request(InternalRequest* req) {
    if (!req) return;
    free(req->original.prompt);
    free(req->original.model);
    free(req->model);
    free(req);
}

