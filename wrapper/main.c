#include "server.h"
#include "globals.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>


int main(int argc, char **argv) {

        if (argc != 3) {
        perror("wrong number of arguments");
        exit(1);
    }
    
    struct Model* models = NULL;

    char *input = strdup(argv[1]);

    char *inner, *outer;
    char *token = strtok_r(input, ";", &outer);
    while (token != NULL) {
        char *tc = strdup(token);

        char *name = strdup(strtok_r(tc, ",", &inner));
        int port = atoi(strtok_r(NULL, ",", &inner));

        struct Model *m = malloc(sizeof(*m));

        m->model = name;
        m->port = port;
        m->next = models;
        models = m;

        free(tc);
        token = strtok_r(NULL, ";", &outer);
    }

    for (struct Model *p = models; p != NULL; p = p->next) {
        printf("%s %d\n", p->model ? p->model : "(null)", p->port);
    }


    printf("%ld\n", (long) models);
    serve(atoi(argv[2]), models);

    while (models) {
        struct Model *next = models->next;
        free(models->model);
        free(models);
        models = next;
    }
    free(input);
    
}
