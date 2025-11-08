#include <stdio.h>
#include <stdlib.h>


typedef struct{
    int port;
    char* model_name;
    struct PortToModel* next;
} PortToModel;

PortToModel* parse_models(char* file_path){
    FILE* fptr;
    fptr = fopen("filename.txt", "r");
    if (fptr == NULL){
        exit(1);
    }
}


