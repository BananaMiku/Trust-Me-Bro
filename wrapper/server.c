#include "globals.h"
#include <stdio.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <regex.h>
#include <pthread.h>
#include <unistd.h>

#define BUFFER_SIZE 104857600

void *handle_client(void *arg) {
  int client_fd = *((int *)arg);
  char *buffer = (char *)malloc(BUFFER_SIZE * sizeof(char));

  // receive request data from client and store into buffer
  ssize_t bytes_received = recv(client_fd, buffer, BUFFER_SIZE, 0);
  if (bytes_received > 0) {
    printf("%s", buffer);
    
    // regex_t regex;
    // regcomp(&regex, "^GET /([^ ]*) HTTP/1", REG_EXTENDED);
    // regmatch_t matches[2];

    // regfree(&regex);
  }
  close(client_fd);
  free(arg);
  free(buffer);
  return NULL;
}


void serve(int port) {
  int server_fd;
  struct sockaddr_in server_addr;
  
  if ((server_fd = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
    perror("die");
    exit(EXIT_FAILURE);
  }

  server_addr.sin_family = AF_INET;
  server_addr.sin_addr.s_addr = INADDR_ANY;
  server_addr.sin_port = htons(port);
  
  if (bind(server_fd, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
    perror("bind failed");
    exit(EXIT_FAILURE);
  }

  if (listen(server_fd, 10) < 0) {
    perror("listen failed");
    exit(EXIT_FAILURE);
  }

  while (1) {
    // client info
    struct sockaddr_in client_addr;
    socklen_t client_addr_len = sizeof(client_addr);
    int *client_fd = malloc(sizeof(int));

    // accept client connection
    if ((*client_fd = accept(server_fd, (struct sockaddr *)&client_addr, &client_addr_len)) < 0) {
      perror("accept failed");
      continue;
    }

    // create a new thread to handle client request
    pthread_t thread_id;
    pthread_create(&thread_id, NULL, handle_client, (void *)client_fd);
    pthread_detach(thread_id);
  }

  close(server_fd);
}







struct Model {
    char *model;
    int port;
    struct Model *next;
};

struct Model *models = NULL;

