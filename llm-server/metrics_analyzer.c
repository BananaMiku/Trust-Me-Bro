// # 1. User sends query 
// #     -query include uuid 
// #     -query gets forwarded to GPU cluster through a LLM gateway?
// # 2. Load Balancing and GPU Cluster Nodes
// #     -load balancer sends query to one of the GPU nodes
// #     -node runs an inference using the LLM model
// # 3. nvidia-smi monitoring
// #     -while job is running, monitor GPU usage with nvidia-smi
// #         -gpu utilization
// #         -memory usage
// #         -power draw 
// #         -gpu temperature
// #         -include stuff like gpu name, SM clocks, memory clocks
// # 4. Data Parsing
// #     -parse nvidia-smi output to extract relevant metrics
// #     -store metrics in a structured format (e.g., JSON, CSV)
// #     -attach uuid
// #     -send stats to TMB server
// # 5. TMB Server Integration
// #     -recieve GPU logs from all GPU instances
// #     -store in database

//brew install curl jansson ossp-uuid
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <curl/curl.h>
#include <jansson.h>
#include <time.h>
#include <stdbool.h>
#include <uuid/uuid.h>

// #define TMB_SERVER_URL "http://tmbserver.example.com/api/gpu_metrics" //will need to change probably
#define TMB_SERVER_URL "http://127.0.0.1:8000/metrics/"
#define LOG_INTERVAL 2 //seconds

json_t* parse_gpu_metrics(const char *csv_output) {
    json_t *metrics = json_array();
    char *copy = strdup(csv_output);
    char *line = strtok(copy, "\n");

    while (line != NULL) {
        char gpu_uuid[64], name[64];
        int util_gpu, util_mem, mem_used, temp;
        float power_draw;

        int parsed = sscanf(line, "%63[^,], %63[^,], %d, %d, %d, %f, %d",
                            gpu_uuid, name, &util_gpu, &util_mem, &mem_used, &power_draw, &temp);
        
        if (parsed == 7) {
            json_t *gpu = json_object();
            json_object_set_new(gpu, "gpu_uuid", json_string(gpu_uuid));
            json_object_set_new(gpu, "name", json_string(name));
            json_object_set_new(gpu, "utilization_gpu", json_integer(util_gpu));
            json_object_set_new(gpu, "utilization_memory", json_integer(util_mem));
            json_object_set_new(gpu, "memory_used", json_integer(mem_used));
            json_object_set_new(gpu, "power_draw", json_real(power_draw));
            json_object_set_new(gpu, "temperature_gpu", json_integer(temp));

            json_array_append_new(metrics, gpu);
        }
        line = strtok(NULL, "\n");
    }

    free(copy);
    return metrics;
}

// Send JSON payload to TMB server using libcurl
int send_to_tmb(json_t *metrics, const char *query_uuid) {
    CURL *curl;
    CURLcode res;
    bool success = false;

    curl_global_init(CURL_GLOBAL_DEFAULT);
    curl = curl_easy_init();

    if (curl) {
        json_t *payload = json_object();
        json_object_set_new(payload, "query_uuid", json_string(query_uuid));
        json_object_set_new(payload, "metrics", metrics);

        char *json_data = json_dumps(payload, 0);

        struct curl_slist *headers = NULL;
        headers = curl_slist_append(headers, "Content-Type: application/json");

        curl_easy_setopt(curl, CURLOPT_URL, TMB_SERVER_URL);
        curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, json_data);

        res = curl_easy_perform(curl);
        if (res != CURLE_OK) {
            fprintf(stderr, "curl_easy_perform() failed: %s\n", curl_easy_strerror(res));
        } else {
            success = true;
        }

        free(json_data);
        json_decref(payload);
        curl_slist_free_all(headers);
        curl_easy_cleanup(curl);
    }

    return success ? 0 : 1;
}

//Generate UUID string
void generate_uuid(char *uuid_str) {
    uuid_t uuid;
    uuid_generate(uuid);
    uuid_unparse_lower(uuid, uuid_str);
}

// Mock function to simulate nvidia-smi output for testing
// char* run_nvidia_smi() {
//     return strdup("GPU-1234, RTX 4090, 90, 60, 24000, 280.5, 70");
// }
char* run_nvidia_smi() {
    FILE *fp;
    char *output = NULL;
    size_t size = 0;

    fp = popen("nvidia-smi --query-gpu=uuid,name,utilization.gpu,utilization.memory,memory.used,power.draw,temperature.gpu --format=csv,noheader,nounits", "r");
    if (fp == NULL) {
        perror("Failed to run nvidia-smi");
        return NULL;
    }

    char buffer[256];
    while (fgets(buffer, sizeof(buffer), fp) != NULL) {
        size_t len = strlen(buffer);
        output = realloc(output, size + len + 1);
        memcpy(output + size, buffer, len);
        size += len;
        output[size] = '\0';
    }

    pclose(fp);
    return output;
}


// Main handler loop
void handle_query(int job_duration) {
    char query_uuid[37];
    generate_uuid(query_uuid);

    printf("Starting job for UUID: %s\n", query_uuid);

    time_t start = time(NULL);

    while (difftime(time(NULL), start) < job_duration) {
        // char *output = run_nvidia_smi();
        // if (output) {
        //     json_t *metrics = parse_gpu_metrics(output);
        //     send_to_tmb(metrics, query_uuid);

        //     free(output);
        //     json_decref(metrics);
        // }
        char *output = run_nvidia_smi();
        if (!output) {
            fprintf(stderr, "No GPU metrics available, skipping iteration.\n");
            sleep(LOG_INTERVAL);
            continue;
        }

        json_t *metrics = parse_gpu_metrics(output);
        if (!metrics) {
            fprintf(stderr, "Failed to parse GPU metrics\n");
            free(output);
            sleep(LOG_INTERVAL);
            continue;
        }

        send_to_tmb(metrics, query_uuid);

        // json_decref(metrics);
        free(output);
        sleep(LOG_INTERVAL);
    }

    printf("Job complete for %s\n", query_uuid);
}


int main() {
    handle_query(10);  
    return 0;
}
