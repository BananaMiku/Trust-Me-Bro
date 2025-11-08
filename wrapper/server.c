#include "server.h"
#include "globals.h"
#include <stdio.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <regex.h>
#include <pthread.h>
#include <unistd.h>
#include <netinet/tcp.h>
#include <netdb.h>
#include <string.h>
#include <signal.h>

#define BUFFER_SIZE 104857600

struct Model *models;

int server_fd;
void sighandle(int sig) {
  close(server_fd);
  exit(0);
}

char *query_nvidia_smi(int port) { 
  // find the PID of the process that is bound to the given TCP port.
  // runs 'nvidia-smi' to filters GPU process table entries for that specific PID

  char cmd[128];
  // Try to find any process listening on the port. -t prints only PIDs.
  // Use -n -P to avoid DNS and service name lookups.
  snprintf(cmd, sizeof(cmd), "lsof -iTCP:%d -sTCP:LISTEN -n -P -t 2>/dev/null", port);

  FILE *fp = popen(cmd, "r");
  if (!fp) {
    return strdup("");
  }

  char pidbuf[64] = {0};
  if (fgets(pidbuf, sizeof(pidbuf), fp) == NULL) {
    pclose(fp);
    return strdup("");
  }
  pclose(fp);

  // strip newline
  size_t len = strlen(pidbuf);
  if (len > 0 && pidbuf[len-1] == '\n') pidbuf[len-1] = '\0';

  //================
  //Use PID to query nvidia-smi for per-process GPU usage
  char smi_cmd[256];
  snprintf(smi_cmd, sizeof(smi_cmd),"nvidia-smi --query-compute-apps=pid,gpu_uuid,used_memory "
            "--format=csv,noheader,nounits | grep '^%s,' 2>/dev/null", pidbuf);

  FILE *smi_fp = popen(smi_cmd, "r");
  if (!smi_fp) {
      perror("Failed to run nvidia-smi");
      return strdup(pidbuf); // Return PID as fallback
  }

  char *output = NULL;
  size_t size = 0;
  char buffer[256];

  while (fgets(buffer, sizeof(buffer), smi_fp) != NULL) {
      size_t chunk = strlen(buffer);
      output = realloc(output, size + chunk + 1);
      memcpy(output + size, buffer, chunk);
      size += chunk;
      output[size] = '\0';
  }

  pclose(smi_fp);

  if (!output) {
      output = strdup(pidbuf);
  }

  return output;
}

char* make_request(char* addr_s, int port, char *req, char* buffer) {
  struct hostent *hp;
  struct sockaddr_in addr;
  int sock;
	int on=1;

  if((hp = gethostbyname(addr_s)) == NULL){
		perror("gethostbyname");
		exit(1);
	}

  bcopy(hp->h_addr, &addr.sin_addr, hp->h_length);
	addr.sin_port = htons(port);
	addr.sin_family = AF_INET;
	sock = socket(PF_INET, SOCK_STREAM, IPPROTO_TCP);
	setsockopt(sock, IPPROTO_TCP, TCP_NODELAY, (const char *)&on, sizeof(int));

	if(sock == -1) {
	  perror("setsockopt");
	  exit(1);
	}

	if(connect(sock, (struct sockaddr *)&addr, sizeof(struct sockaddr_in)) == -1){
		perror("connect");
		exit(1);
	}
	
	write(sock, req, strlen(req));
	bzero(buffer, BUFFER_SIZE);
	
	char *res = malloc(BUFFER_SIZE);
	int totallen = 0;
	int len;
	while ((len = read(sock, buffer, BUFFER_SIZE - 1)) != 0){
	  totallen += len*4;
	  buffer = realloc(buffer, totallen);
	  strcat(res, buffer);
	}

	return res;
}

struct PollNvidiaSmiArgs {
  int port;
  int *done;
};
void *poll_nvidia_smi(void* _args) {
  struct PollNvidiaSmiArgs *args = (struct PollNvidiaSmiArgs*)_args;
  int port = args->port;

  while (!*args->done) {
    char *buffer = (char *)malloc(BUFFER_SIZE * sizeof(char));
  
    char *something = query_nvidia_smi(port); //port is the port that the model server is running on
    char *hostname = "https://ourserver.com";

    char* req;
    sprintf(req,
      "GET %s HTTP/1.0\r\n"
      "Host: %s\r\n"
      "Content-type: text/plain\r\n"
      "Content-length: %ld\r\n\r\n"
      "%s\r\n", "/", hostname, strlen(something), something);
  
    char *res = make_request(hostname, 80, req, buffer);
    free(res);
    sleep(1);
  }
  return NULL;
}



void *handle_client(void *arg) {
  int client_fd = *((int *)arg);
  char *buffer = (char *)malloc(BUFFER_SIZE * sizeof(char));

  // receive request data from client and store into buffer
  ssize_t bytes_received = recv(client_fd, buffer, BUFFER_SIZE, 0);
  if (bytes_received > 0) {
    
    char *body = strstr(buffer, "\r\n\r\n");
    if (body == NULL) {
      perror("bad request");
      exit(1);
    }
    body += 4;

    printf("%s\n", buffer);
    printf("%s\n", body);
    
    InternalRequest *req = parse_internal_request(body);
    
    // get port from model
    struct Model *model;
    for (struct Model *p = models; p != NULL; p = p->next) {
      if (strcmp(p->model, req->model)) {
        model = p;
        break;
      }
    }
    if (model == NULL) {
      perror("unknown model");
      exit(0);
    }
    
    printf("hi5\n");
    printf("%d, %ld\n", (int)((body - buffer)), strlen(buffer));
    printf("%.*s\n", (int)((body - buffer)), buffer);
    printf("hi\n");
    printf("%ld\n", (long)req);
    printf("hi\n");
    printf("%s\n", req->original);
    printf("hi\n");
    char* newreq;
    sprintf(newreq, "%.*s%s", (int)((body - buffer)/4+1), buffer, req->original);

    // start profiling before we make the request
    printf("hi7\n");
    fflush(stdout);
    pthread_t thread_id;
    int done = 0;
    struct PollNvidiaSmiArgs args = {
      .done = &done,
      .port = model->port,
    };
    printf("hi15\n");
    pthread_create(&thread_id, NULL, poll_nvidia_smi, &args);
    printf("hi16\n");

    
    printf("hi8\n");
    char* res = make_request("localhost", model->port, newreq, buffer);
    done = 1;
    write(client_fd, res, strlen(res));
    close(client_fd);

    printf("hi9\n");
    free(res);
    free(newreq);
  }
  close(client_fd);
  free(arg);
  free(buffer);
  return NULL;
}


void serve(int port, struct Model* _models) {
  models = _models;
  printf("%ld\n", (long) models);
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

  signal(SIGINT, sighandle);

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
